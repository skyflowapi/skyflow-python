# NOTE: hand-patched, not Fern-generated content. Fern originally emitted a runtime
# metadata.version("skyflow.generated.rest") lookup here, but this code is bundled into the
# skyflow (v2) and v3 wheels via a build_py hook rather than published under that distribution
# name, so the lookup always raised PackageNotFoundError on import. Hardcoded until the Fern
# generator config (skyflow-fern-config) is updated to stop emitting a runtime lookup here.
__version__ = "0.0.9"
