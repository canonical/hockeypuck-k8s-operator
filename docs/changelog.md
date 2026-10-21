# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

Each revision is versioned by the date of the revision.

## 2026-10-21

- Migrated the charm and rock to paas-charm 2.0 and Ubuntu 26.04 LTS. The `app-port` and
  `metrics-port` options are removed. The ports are now fixed in `paas-config.yaml` (HTTP on
  11371, metrics on 9626), so unset both options before refreshing. The prefix tree moved to
  `/app-data/ptree`.

## 2026-04-16

- Added landing pages for How-to and Reference documentation sections.

## 2025-12-17

- Moved charm-architecture.md from Explanation to Reference category.

## 2025-05-27

- Use a local constant for workload container name instead of reading it from upstream paas-charm.
- Address review comments provided by charmcraft team during the enlisting process.

## 2025-05-22

- Fix broken links found in Charmhub docs.

## 2025-05-21

- Update promote charm workflow.

## 2025-05-02

- Added security documentation.

## 2025-04-29

- Fixed issues found in the COS integration during staging.

## 2025-04-24

- Modified publish charm workflow to use `2.2/edge` track instead of `latest/edge`

## 2025-04-21

- Added documentation for Hockeypuck.

## 2025-04-21

- Cleaned up GitHub workflows for Hockeypuck and modified the charm source code to 
remove business logic from constructors.

## 2025-04-16

- Changelog added for tracking changes.
