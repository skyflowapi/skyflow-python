# Changelog

All notable changes to this project will be documented in this file.

## [1.15.1] - 2023-12-07
## Fixed
- Not receiving tokens when calling Get with options tokens as true.

## [1.15.0] - 2023-10-30
## Added
- options tokens support for Get method.

## [1.14.0] - 2023-09-29
## Added
- Support for different BYOT modes in Insert method.

## [1.13.1] - 2023-09-14
### Changed
- Add `request_index` in responses for insert method.

## [1.13.0] - 2023-09-04
### Added
- Added new Query method.

## [1.12.0] - 2023-09-01
### Added
- Support for Bulk request with Continue on Error in Detokenize Method
- Support for Continue on Error in Insert Method

## [1.11.0] - 2023-08-25
### Added
- Support for BYOT in Insert method.

## [1.10.1] - 2023-07-28
### Fixed
- Fixed delete method

## [1.10.0] - 2023-07-21
### Added
- Added delete method

## [1.9.2] - 2023-06-22
### Fixed
- Multiple record error in get method

## [1.9.1] - 2023-06-07
### Fixed
- Fixed bug in metrics

## [1.9.0] - 2023-06-07
### Added
- Added redaction type in detokenize

## [1.8.1] - 2023-03-17
### Removed
- removed grace period logic in bearer token generation

## [1.8.0] - 2023-01-10
### Added
- update and get methods.

## [1.7.0] - 2022-12-07
### Added
- `upsert` support for insert method.

## [1.6.2] - 2022-06-28

### Added
- Copyright header to all files
- Security email in README

## [1.6.1] - 2022-05-17

### Fixed

- Insert with multiple records returning invalid output

## [1.6.0] - 2022-04-12

### Added

- support for application/x-www-form-urlencoded and multipart/form-data content-type's in connections.

## [1.5.1] - 2022-03-29

### Added

- Validation to token obtained from `tokenProvider`

### Fixed

- Request headers not getting overridden due to case sensitivity

## [1.5.0] - 2022-03-22

### Changed

- `getById` changed to `get_by_id`
- `invokeConnection`changed to `invoke_connection`
- `generateBearerToken` changed to `generate_bearer_token`
- `generateBearerTokenDromCreds` changed to `generate_bearer_token_from_creds`
- `isExpired` changed to `is_expired`
- `setLogLevel` changed to `set_log_level`

### Removed

- `isValid` function
- `GenerateToken` function

## [1.4.0] - 2022-03-15

### Changed

- deprecated `isValid` in favour of `isExpired`

## [1.3.0] - 2022-02-24

### Added

- Request ID in error logs and error responses for API Errors
- Caching to accessToken token
- `isValid` method for validating Service Account bearer token

## [1.2.1] - 2022-01-18

### Fixed

- `generateBearerTokenFromCreds` raising error "invalid credentials" on correct credentials

## [1.2.0] - 2022-01-04

### Added

- Logging functionality
- `setLogLevel` function for setting the package-level LogLevel
- `generateBearerTokenFromCreds` function which takes credentials as string

### Changed

- Renamed and deprecated `GenerateToken` in favor of `generateBearerToken`
- Make `vaultID` and `vaultURL` optional in `Client` constructor

## [1.1.0] - 2021-11-10

### Added

- `insert` vault API
- `detokenize` vault API
- `getById` vault API
- `invokeConnection`

## [1.0.1] - 2021-10-26

### Changed

- Package description

## [1.0.0] - 2021-10-19

### Added

- Service Account Token generation
