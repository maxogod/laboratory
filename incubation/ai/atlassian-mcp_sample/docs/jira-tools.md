# Jira Integration Tools

This document describes the integrated Jira capabilities, available tools, their schemas, parameters, and design behaviors.

## Overview
The Jira integration reads, creates and edits tickets via **Jira REST API v3**.
- **Read Operations** never ask for approval.
- **Write Operations** always ask for approval. See [Approvals](../README.md#approvals), including the extra step for the Antigravity App and IDE.

---

## Configuration & Setup
The integration initializes gracefully based on environment variables. If any variables are missing, the server starts up fine but will return clear, polite error strings explaining what is missing if a Jira tool is called.

Ensure the following variables are configured in your `.env` file:
```env
JIRA_BASE_URL=https://your-domain.atlassian.net
ATLASSIAN_EMAIL=user@company.com
JIRA_API_TOKEN=your_jira_api_token
```

The token uses your Jira account's permissions. A scoped token needs `read:jira-work` and `write:jira-work`.

---

## Available Tools

### 1. `jira_read_ticket`
Reads details of a Jira ticket (issue) by its ID or key (e.g., `PROJ-123`). Does not ask for approval.

* **Parameters:**
  * `ticket_id` (string, required): The Jira issue key or ID.
* **Key Features:**
  * Parses **Atlassian Document Format (ADF)** recursively into readable text. This is a simplified view: formatting such as bold, links and tables is not returned.
  * Gracefully catches permissions, unconfigured states, or missing issues and returns polite, formatted strings instead of crashing.

---

### 2. `jira_search_tickets`
Lists and searches backlog tickets (not `Done`) matching a keyword/topic or specific label. Does not ask for approval.

* **Parameters:**
  * `query` (string, optional): Keywords/phrases to search for in issue fields.
  * `label` (string, optional): A specific label to filter issues by.
  * *Note: At least one search parameter (`query` or `label`) must be provided.*
* **Key Features:**
  * Performs dynamically compiled **JQL (Jira Query Language)** searches.
  * Automatically appends `statusCategory != Done` to restrict results strictly to the project backlog.

---

### 3. `jira_create_ticket`
Creates a ticket and returns its key and URL. Always asks for approval.

* **Parameters:**
  * `project_key` (string, required): The key of the project (e.g., `PROJ`).
  * `summary` (string, required): The ticket title.
  * `issue_type` (string, required): The exact issue type name used by the project (e.g., `Task`, `Bug`).
  * `description` (string, optional): The description, in Markdown.
  * `labels` (list of strings, optional): Labels to set on the ticket.

---

### 4. `jira_edit_ticket`
Overwrites the summary, description and/or labels of a ticket. Always asks for approval.

* **Parameters:**
  * `ticket_id` (string, required): The Jira issue key or ID.
  * `summary` (string, optional): The new title.
  * `description` (string, optional): The complete new description, in Markdown. An empty string clears it.
  * `labels` (list of strings, optional): The complete new list of labels. An empty list clears them.
  * *Note: At least one field must be provided.*
* **Key Features:**
  * Fields that are not provided are left untouched.
  * Status, assignee and other fields cannot be changed with this tool.

---

## Markdown Support
Jira REST API v3 requires descriptions in ADF, so `jira_create_ticket` and `jira_edit_ticket` convert Markdown:

* **Supported:** headings, lists, fenced code blocks, horizontal rules, bold, italic, inline code and links.
* **Flattened:** nested lists become a single level.
* **Kept as literal text:** anything else, including tables.

Rewriting a description replaces it entirely, so anything Markdown cannot express, such as panels, images and mentions, is lost.
