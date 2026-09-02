import json
import sys

import griffe

CONTRACTS = {
    "skyvault": {
        "package": "skyflow",
        "search": "skyvault",
        "modules": [
            "skyflow",
            "skyflow.client",
            "skyflow.vault.data",
            "skyflow.vault.controller",
            "skyflow.vault.connection",
            "skyflow.vault.tokens",
            "skyflow.vault.detect",
            "skyflow.service_account",
            "skyflow.error",
            "skyflow.utils.enums",
        ],
    },
    "flowvault": {
        "package": "skyflow_flowvault",
        "search": "flowvault",
        "modules": [
            "skyflow_flowvault",
            "skyflow_flowvault.client",
            "skyflow_flowvault.vault.data",
            "skyflow_flowvault.vault.controller",
            "skyflow_flowvault.service_account",
            "skyflow_flowvault.error",
            "skyflow_flowvault.utils.enums",
        ],
    },
}

USAGE = "usage: griffe_contract.py {dump|check} <module> <baseline_path>"
ARG_COUNT = 3


def _keep_and_containers(modules):
    keep = set(modules)
    containers = set()
    for path in modules:
        parts = path.split(".")
        for i in range(1, len(parts)):
            ancestor = ".".join(parts[:i])
            if ancestor not in keep:
                keep.add(ancestor)
                containers.add(ancestor)
    return keep, containers


def _resolve(obj):
    if obj.is_alias:
        try:
            return obj.final_target
        except Exception:
            return None
    return obj


def _is_real_submodule(member):
    return not member.is_alias and member.is_module


def _public(name):
    return name == "__init__" or not name.startswith("_")


def _describe(obj):
    target = _resolve(obj)
    if target is None:
        return f"alias -> {obj.target_path}"
    if target.is_function:
        params = []
        for param in target.parameters:
            piece = param.name
            if param.annotation is not None:
                piece += f": {param.annotation}"
            if param.default is not None:
                piece += f" = {param.default}"
            params.append(piece)
        returns = f" -> {target.returns}" if target.returns is not None else ""
        return f"def ({', '.join(params)}){returns}"
    if target.is_class:
        bases = ", ".join(str(base) for base in target.bases)
        return f"class ({bases})"
    if target.is_attribute:
        annotation = f": {target.annotation}" if target.annotation is not None else ""
        keep_value = "class-attribute" in target.labels and target.value is not None
        value = f" = {target.value}" if keep_value else ""
        return f"attr{annotation}{value}"
    if target.is_module:
        return "module"
    return target.kind.value


def _emit_members(module, surface, is_container):
    if is_container:
        return
    for name in sorted(module.members):
        if not _public(name):
            continue
        member = module.members[name]
        if _is_real_submodule(member):
            continue
        surface[member.path] = _describe(member)
        target = _resolve(member)
        if target is not None and target.is_class:
            for child_name in sorted(target.members):
                if not _public(child_name):
                    continue
                surface[f"{member.path}.{child_name}"] = _describe(target.members[child_name])


def build_surface(module_key):
    config = CONTRACTS[module_key]
    keep, containers = _keep_and_containers(config["modules"])

    collection = griffe.ModulesCollection()
    griffe.load("common", search_paths=["."], modules_collection=collection)
    root = griffe.load(
        config["package"],
        search_paths=[config["search"], "."],
        modules_collection=collection,
        resolve_aliases=True,
        resolve_external=True,
    )

    surface = {}

    def walk(module):
        if module.path in keep and module.path not in containers:
            _emit_members(module, surface, is_container=False)
        for name in sorted(module.members):
            member = module.members[name]
            if _is_real_submodule(member) and member.path in keep:
                walk(member)

    walk(root)
    return dict(sorted(surface.items()))


def dump(module_key, baseline_path):
    surface = build_surface(module_key)
    with open(baseline_path, "w", encoding="utf-8") as handle:
        json.dump(surface, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print(f"Wrote {len(surface)} public members to {baseline_path}")


def check(module_key, baseline_path):
    current = build_surface(module_key)
    try:
        with open(baseline_path, encoding="utf-8") as handle:
            baseline = json.load(handle)
    except FileNotFoundError:
        print(f"ERROR: no committed baseline at {baseline_path}.")
        print(f"Generate it with: ci-scripts/contract-snapshot-update.sh {module_key}")
        return 1

    removed = sorted(set(baseline) - set(current))
    added = sorted(set(current) - set(baseline))
    changed = sorted(k for k in set(baseline) & set(current) if baseline[k] != current[k])

    if not (removed or added or changed):
        print(f"OK: {module_key} public API surface matches the committed contract ({len(current)} members).")
        return 0

    print(f"Public API contract drift detected for {module_key} ({CONTRACTS[module_key]['package']}):\n")
    for key in removed:
        print(f"  - REMOVED  {key}  ::  {baseline[key]}")
    for key in added:
        print(f"  + ADDED    {key}  ::  {current[key]}")
    for key in changed:
        print(f"  ~ CHANGED  {key}")
        print(f"      from: {baseline[key]}")
        print(f"      to:   {current[key]}")
    print("\nRemoved/changed entries are breaking; added entries are new public surface.")
    print(f"If this change is intentional, run:  ci-scripts/contract-snapshot-update.sh {module_key}")
    print("then review and commit the updated baseline alongside your code change.")
    return 1


def main(argv):
    if len(argv) != ARG_COUNT or argv[0] not in ("dump", "check") or argv[1] not in CONTRACTS:
        print(USAGE)
        return 2
    command, module_key, baseline_path = argv
    if command == "dump":
        dump(module_key, baseline_path)
        return 0
    return check(module_key, baseline_path)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
