# Changelog

All notable changes to this project will be documented in this file.

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
