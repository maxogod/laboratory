---
name: attlassian-mcp-use-guide
description: How to use the 123mcp tools for Jira, Bitbucket and the 123ui-kit storybook. Use when reading, creating or editing Jira tickets or Bitbucket pull requests, or when looking up 123ui-kit components.
---

# Using the 123mcp tools

## Always show content before writing

Before calling `jira_create_ticket`, `jira_edit_ticket`, `bitbucket_create_pr` or `bitbucket_edit_pr`, write out in your response exactly what will be sent:

- **Creating:** every field, in full.
- **Editing:** the current value and the new value of every field that changes. Read the ticket or pull request first to get the current values.

Never abbreviate the content or refer to an earlier draft. If the user rejects the tool call, what you showed is what they can still copy and use by hand, so it must be complete and ready to paste.

You will normally be asked for approval on every write. That prompt does not replace showing the content, and it may not appear if the user allowed the tool for the session, so never skip this step.

## When the user rejects a write

Do not retry the same call. Leave the content in the conversation and ask whether they want changes or will apply it themselves.

## Which tools need approval

| Tools | Approval |
| --- | --- |
| `jira_read_ticket`, `jira_search_tickets`, `bitbucket_read_pr`, `bitbucket_get_pr_diff`, `list_storybook_components`, `read_storybook_component_example` | Not needed, so use them freely to gather context |
| `jira_create_ticket`, `bitbucket_create_pr` | Every call |
| `jira_edit_ticket`, `bitbucket_edit_pr` | Every call. Previous values are overwritten |

## Editing safely

- Only pass the fields that change. Omitted fields keep their current value.
- `description` and `labels` replace the whole value, so include everything that should remain.
- Avoid rewriting a Jira description for a small change elsewhere. `jira_read_ticket` returns simplified text, and a rewrite loses formatting Markdown cannot express, such as tables, panels, images and mentions. Warn the user if the ticket may contain any.
- Jira descriptions support headings, flat lists, fenced code, rules, bold, italic, inline code and links. Nested lists are flattened.

## Creating safely

- Search with `jira_search_tickets` first to avoid duplicating a ticket. It only covers tickets that are not Done.
- `issue_type` must exactly match a name the project uses. If you don't know it, ask the user.
- The source branch of a pull request must already be pushed. Without `destination_branch`, it targets the repository's main branch.
- Set reviewers, assignees and ticket status in the Bitbucket or Jira UI. These tools cannot change them.

## When a call fails

Tools return errors as text beginning with `Error:` or `Unexpected error`. Tell the user what happened, then:

- **Rejected by the API** (invalid field, permission denied): fix the cause, or explain it, then show the content again.
- **Connection failure or unexpected error:** the write may have gone through. Read or search first so you don't create a duplicate or repeat an edit.
- **Permission denied on a write when reads work:** the user's token probably lacks write scopes. Point them to the project's README.

## Pull request context

- `bitbucket_read_pr` returns metadata, description, commits and comments together. Use `bitbucket_get_pr_diff` for the code changes.
- Base a pull request description on the commits and diff, not on assumptions.
- Long pull requests may be cut off: commits and comments only include the first page of results, so don't treat those lists as complete.

## 123ui-kit components

Call `list_storybook_components` to find a component, then pass its URL to `read_storybook_component_example` for usage examples. Prefer an existing component over building a new one.
