# Bitbucket Integration Tools

This document describes the integrated Bitbucket capabilities, available tools, their schemas, parameters, and design behaviors.

## Overview
The Bitbucket integration reads, creates and edits pull requests via the **Bitbucket Cloud REST API v2**.
- **Read Operations** never ask for approval.
- **Write Operations** always ask for approval. See [Approvals](../README.md#approvals), including the extra step for the Antigravity App and IDE.

---

## Configuration & Setup
The integration initializes gracefully based on environment variables. If any variables are missing, the server starts up fine but will return clear, polite error strings explaining what is missing if a Bitbucket tool is called.

Ensure the following variables are configured in your `.env` file:
```env
ATLASSIAN_EMAIL=user@company.com
BITBUCKET_WORKSPACE=your_workspace_slug
BITBUCKET_TOKEN=your_bitbucket_token
```

The token needs the `read:pullrequest:bitbucket` and `write:pullrequest:bitbucket` scopes.

---

## Available Tools

### 1. `bitbucket_read_pr`
Reads a pull request's metadata, description, commits and comments. Does not ask for approval.

* **Parameters:**
  * `repo_slug` (string, required): The slug of the repository (e.g., "my-project").
  * `pull_request_id` (integer, required): The numeric ID of the pull request.
* **Key Features:**
  * Fetches the title, description, author, status and dates of the pull request.
  * Lists commits, and comments in chronological order.
  * Only the first page of commits and comments is returned, as Bitbucket paginates both.
  * Gracefully handles errors such as missing permissions, incorrect configuration, or non-existent pull requests, returning a clear message instead of crashing.

### 2. `bitbucket_get_pr_diff`
Gets the raw diff of a pull request. Does not ask for approval.

* **Parameters:**
  * `repo_slug` (string, required): The slug of the repository (e.g., "my-project").
  * `pull_request_id` (integer, required): The numeric ID of the pull request.

### 3. `bitbucket_create_pr`
Creates a pull request and returns its ID and URL. Always asks for approval.

* **Parameters:**
  * `repo_slug` (string, required): The slug of the repository.
  * `title` (string, required): The pull request title.
  * `source_branch` (string, required): The branch containing the changes. It must already be pushed.
  * `destination_branch` (string, optional): The target branch. Defaults to the repository's main branch.
  * `description` (string, optional): The description, in Markdown.
  * `close_source_branch` (boolean, optional): Whether to delete the source branch after merging. Defaults to `false`.
* **Key Features:**
  * Reviewers cannot be set with this tool. Add them in Bitbucket.

### 4. `bitbucket_edit_pr`
Overwrites the title and/or description of a pull request. Always asks for approval.

* **Parameters:**
  * `repo_slug` (string, required): The slug of the repository.
  * `pull_request_id` (integer, required): The numeric ID of the pull request.
  * `title` (string, optional): The new title.
  * `description` (string, optional): The complete new description, in Markdown. An empty string clears it.
  * *Note: At least one of `title` or `description` must be provided.*
* **Key Features:**
  * Fields that are not provided keep their current value.
  * Reads the pull request first and resends its reviewers, because Bitbucket can remove reviewers omitted from an update.
