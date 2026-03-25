#!/usr/bin/env python3
"""Patch OpenHands V0/V1 prompts and routing to prefer internet tools for external resources."""

from pathlib import Path
import sys

INTERACTIVE_TARGET = Path(
    "/app/openhands/agenthub/codeact_agent/prompts/system_prompt_interactive.j2"
)
SYSTEM_TARGET = Path(
    "/app/openhands/agenthub/codeact_agent/prompts/system_prompt.j2")
APP_SERVER_TARGET = Path(
    "/app/openhands/app_server/app_conversation/live_status_app_conversation_service.py"
)
APP_SERVER_SKILL_TARGET = Path(
    "/app/openhands/app_server/app_conversation/app_conversation_service_base.py"
)

INTERACTIVE_PATCH_SNIPPET = """* When the user asks for information or files from a public external project, website, repository, package, release, or other internet resource, treat it as an external browsing task instead of a local workspace exploration task.
  1. Prefer the available web, browser, or MCP research tools first when the target should come from the internet.
  2. Do NOT search /workspace or the local filesystem for similarly named files unless the user explicitly asks about local files or has already cloned the target repository into the workspace.
  3. Preserve the user's exact external target clues, including filenames, extensions, artifact names, version strings, and path fragments.
  4. If the user did not provide a URL, do NOT invent one. Search first using the user's exact clue set, then browse the discovered result.
"""

INTERACTIVE_ANCHOR = """* When the user instructions are high-level or vague, explore the codebase before implementing solutions or interacting with users to figure out the best approach.
  1. Read and follow project-specific documentation (rules.md, README, etc.) before making assumptions about workflows, conventions, or feature implementations.
  2. Deliver complete, production-ready solutions rather than partial implementations; ensure all components work together before presenting results.
  3. Check for existing solutions and test cases before creating new implementations; leverage established patterns rather than reinventing functionality.
"""

SYSTEM_PATCH_SNIPPET = """
<EXTERNAL_RESOURCE_ROUTING>
* When the user asks for information, documentation, files, archives, release assets, or other resources from an external website or project, treat it as an internet task.
* Prefer the available web, browser, and MCP research tools before searching the local workspace or filesystem for similarly named files.
* Preserve exact external resource clues from the user, including filenames, extensions, version strings, artifact names, and path fragments, when selecting tools and writing tool arguments.
* If the user did not provide a URL, do NOT invent one. Search first using the user's exact clue set, then browse the discovered result.
* Do NOT search /workspace for external project files unless the user explicitly asks about local files or the target repository has already been cloned into the workspace.
</EXTERNAL_RESOURCE_ROUTING>
"""

SYSTEM_ANCHOR = """</ROLE>
"""

APP_SERVER_CALL_SNIPPET = """        # Create agent with context
        agent = self._create_agent_with_context(
            llm,
            agent_type,
            system_message_suffix,
            mcp_config,
            user.condenser_max_size,
            secrets=secrets,
            git_provider=git_provider,
            working_dir=working_dir,
        )
"""

APP_SERVER_CALL_REPLACEMENT = """        # Create agent with context
        effective_system_message_suffix = system_message_suffix
        if not selected_repository:
            no_repo_external_resource_suffix = (
                "No repository is connected in this conversation. "
                "References to named public projects, repositories, packages, files, "
                "archives, release assets, documentation, or websites should be "
                "treated as external internet resources, not local workspace files. "
                "Preserve exact filenames, extensions, artifact names, version "
                "strings, and path clues from the user's request when choosing "
                "tools and writing tool arguments. If the user did not provide "
                "a URL, do not invent one; search first using the user's exact "
                "clue set, then browse the discovered result. "
                "For those requests, prefer MCP and browser tools before searching "
                "/workspace or the local filesystem."
            )
            effective_system_message_suffix = (
                no_repo_external_resource_suffix
                if not effective_system_message_suffix
                else no_repo_external_resource_suffix
                + "\\n\\n"
                + effective_system_message_suffix
            )

        agent = self._create_agent_with_context(
            llm,
            agent_type,
            effective_system_message_suffix,
            mcp_config,
            user.condenser_max_size,
            secrets=secrets,
            git_provider=git_provider,
            working_dir=working_dir,
            selected_repository=selected_repository,
        )
"""

APP_SERVER_SIGNATURE_SNIPPET = """    def _create_agent_with_context(
        self,
        llm: LLM,
        agent_type: AgentType,
        system_message_suffix: str | None,
        mcp_config: dict,
        condenser_max_size: int | None,
        secrets: dict[str, SecretValue] | None = None,
        git_provider: ProviderType | None = None,
        working_dir: str | None = None,
    ) -> Agent:
"""

APP_SERVER_SIGNATURE_REPLACEMENT = """    def _create_agent_with_context(
        self,
        llm: LLM,
        agent_type: AgentType,
        system_message_suffix: str | None,
        mcp_config: dict,
        condenser_max_size: int | None,
        secrets: dict[str, SecretValue] | None = None,
        git_provider: ProviderType | None = None,
        working_dir: str | None = None,
        selected_repository: str | None = None,
    ) -> Agent:
"""

APP_SERVER_DEFAULT_TOOLS_SNIPPET = """        else:
            agent = Agent(
                llm=llm,
                tools=get_default_tools(enable_browser=True),
                system_prompt_kwargs={'cli_mode': False},
                condenser=condenser,
                mcp_config=mcp_config,
            )
"""

APP_SERVER_DEFAULT_TOOLS_REPLACEMENT = """        else:
            default_tools = (
                []
                if (not selected_repository and mcp_config)
                else get_default_tools(enable_browser=True)
            )
            agent = Agent(
                llm=llm,
                tools=default_tools,
                system_prompt_kwargs={'cli_mode': False},
                condenser=condenser,
                mcp_config=mcp_config,
            )
"""

APP_SERVER_MCP_FILTER_ANCHOR = (
    "        llm, mcp_config = await self._configure_llm_and_mcp(user, llm_model)\n"
)

APP_SERVER_MCP_FILTER_SNIPPET = """        if (
            not selected_repository
            and user.mcp_config
            and (
                user.mcp_config.sse_servers
                or user.mcp_config.shttp_servers
                or user.mcp_config.stdio_servers
            )
            and mcp_config.get('mcpServers')
        ):
            custom_only_mcp_servers = {
                name: config
                for name, config in mcp_config['mcpServers'].items()
                if name not in {'default', 'tavily'}
            }
            if custom_only_mcp_servers:
                mcp_config = {'mcpServers': custom_only_mcp_servers}
"""

APP_SERVER_SKILL_FILTER_SNIPPET = """            if not selected_repository:
                all_skills = [
                    skill for skill in all_skills
                    if skill.name in {'work_hosts'}
                ]
"""

APP_SERVER_SKILL_FILTER_ANCHOR = """            all_skills = await load_skills_from_agent_server(
                agent_server_url=agent_server_url,
                session_api_key=sandbox.session_api_key,
                project_dir=project_dir,
                org_config=org_config,
                sandbox_config=sandbox_config,
                load_public=True,
                load_user=True,
                load_project=True,
                load_org=True,
            )
"""

APP_SERVER_TITLE_CALLBACK_BLOCK = """            # Always ensure SetTitleCallbackProcessor is included
            has_set_title_processor = any(
                isinstance(processor, SetTitleCallbackProcessor)
                for processor in processors
            )
            if not has_set_title_processor:
                processors.append(SetTitleCallbackProcessor())
"""

APP_SERVER_TITLE_CALLBACK_REPLACEMENT = """            # Disable automatic title-generation callbacks in OH_SHOP.
            # They add noisy LLM traffic and have been a source of callback-db
            # errors during fresh-session MCP proof runs.
"""


def _patch_target(
    target: Path,
    *,
    anchor: str,
    patch_snippet: str,
    replacement: str | None = None,
    backup_suffix: str,
    label: str,
) -> tuple[bool, str]:
    if not target.exists():
        return False, f"target file not found: {target}"

    text = target.read_text(encoding="utf-8")
    if patch_snippet in text:
        return True, f"{label} patch already present"

    if anchor not in text:
        return False, (
            f"expected {label} prompt block not found; refusing blind patch")

    backup = target.with_suffix(target.suffix + backup_suffix)
    if not backup.exists():
        backup.write_text(text, encoding="utf-8")

    final_replacement = replacement or (anchor + "\n" + patch_snippet)
    target.write_text(
        text.replace(anchor, final_replacement, 1),
        encoding="utf-8",
    )
    return True, f"applied {label} patch"


def _patch_app_server() -> tuple[bool, str]:
    target = APP_SERVER_TARGET
    if not target.exists():
        return False, f"target file not found: {target}"

    text = target.read_text(encoding="utf-8")
    original = text
    changed = False

    if "no_repo_external_resource_suffix" not in text:
        replacements = (
            (APP_SERVER_CALL_SNIPPET, APP_SERVER_CALL_REPLACEMENT),
            (APP_SERVER_SIGNATURE_SNIPPET, APP_SERVER_SIGNATURE_REPLACEMENT),
            (APP_SERVER_DEFAULT_TOOLS_SNIPPET,
             APP_SERVER_DEFAULT_TOOLS_REPLACEMENT),
        )
        for old, new in replacements:
            if old not in text:
                return False, "expected app-server block not found; refusing blind patch"
            text = text.replace(old, new, 1)
        changed = True
    else:
        legacy_suffixes = (
            '"References to named public projects, repositories, packages, READMEs, "\n'
            '                "release assets, documentation, or websites should be treated as "\n'
            '                "external internet resources, not local workspace files. "\n'
            '                "For those requests, prefer MCP and browser tools before searching "\n'
            '                "/workspace or the local filesystem."',
            '"References to named public projects, repositories, packages, READMEs, "\n'
            '                "release assets, documentation, or websites should be treated as "\n'
            '                "external internet resources, not local workspace files. "\n'
            '                "For those requests, prefer MCP and browser tools before searching "\n'
            '                "/workspace or the local filesystem."',
        )
        replacement_suffix = (
            '"References to named public projects, repositories, packages, files, "\n'
            '                "archives, release assets, documentation, or websites should be "\n'
            '                "treated as external internet resources, not local workspace files. "\n'
            '                "Preserve exact filenames, extensions, artifact names, version "\n'
            '                "strings, and path clues from the user\'s request when choosing "\n'
            '                "tools and writing tool arguments. If the user did not provide "\n'
            '                "a URL, do not invent one; search first using the user\'s exact "\n'
            '                "clue set, then browse the discovered result. "\n'
            '                "For those requests, prefer MCP and browser tools before searching "\n'
            '                "/workspace or the local filesystem."')
        for legacy_suffix in legacy_suffixes:
            if legacy_suffix in text:
                text = text.replace(legacy_suffix, replacement_suffix, 1)
                changed = True
                break

    if "custom_only_mcp_servers" not in text:
        if APP_SERVER_MCP_FILTER_ANCHOR not in text:
            return False, "expected MCP config block not found; refusing blind patch"
        text = text.replace(
            APP_SERVER_MCP_FILTER_ANCHOR,
            APP_SERVER_MCP_FILTER_ANCHOR + APP_SERVER_MCP_FILTER_SNIPPET,
            1,
        )
        changed = True

    if "Disable automatic title-generation callbacks in OH_SHOP." not in text:
        if APP_SERVER_TITLE_CALLBACK_BLOCK not in text:
            return False, "expected title callback block not found; refusing blind patch"
        text = text.replace(
            APP_SERVER_TITLE_CALLBACK_BLOCK,
            APP_SERVER_TITLE_CALLBACK_REPLACEMENT,
            1,
        )
        changed = True

    if not changed:
        return True, "app-server routing patch already present"

    backup = target.with_suffix(target.suffix + ".bak_oh_shop_ext_v1")
    if not backup.exists():
        backup.write_text(original, encoding="utf-8")

    target.write_text(text, encoding="utf-8")
    return True, "applied app-server routing patch"


def _patch_skill_loader_target() -> tuple[bool, str]:
    target = APP_SERVER_SKILL_TARGET
    if not target.exists():
        return False, f"target file not found: {target}"

    text = target.read_text(encoding="utf-8")
    if "if not selected_repository:\n                all_skills = [" in text:
        return True, "app-server skill patch already present"

    if APP_SERVER_SKILL_FILTER_ANCHOR not in text:
        return False, "expected skill loading block not found; refusing blind patch"

    backup = target.with_suffix(target.suffix + ".bak_oh_shop_skill_v1")
    if not backup.exists():
        backup.write_text(text, encoding="utf-8")

    target.write_text(
        text.replace(
            APP_SERVER_SKILL_FILTER_ANCHOR,
            APP_SERVER_SKILL_FILTER_ANCHOR + APP_SERVER_SKILL_FILTER_SNIPPET,
            1,
        ),
        encoding="utf-8",
    )
    return True, "applied app-server skill patch"


def main() -> int:
    interactive_ok, interactive_msg = _patch_target(
        INTERACTIVE_TARGET,
        anchor=INTERACTIVE_ANCHOR,
        patch_snippet=INTERACTIVE_PATCH_SNIPPET,
        backup_suffix=".bak_oh_shop_ext",
        label="interactive",
    )
    if not interactive_ok:
        print(interactive_msg, file=sys.stderr)
        return 1

    system_ok, system_msg = _patch_target(
        SYSTEM_TARGET,
        anchor=SYSTEM_ANCHOR,
        patch_snippet=SYSTEM_PATCH_SNIPPET,
        replacement=SYSTEM_ANCHOR + SYSTEM_PATCH_SNIPPET,
        backup_suffix=".bak_oh_shop_ext_base",
        label="system",
    )
    if not system_ok:
        print(system_msg, file=sys.stderr)
        return 1

    app_server_ok, app_server_msg = _patch_app_server()
    if not app_server_ok:
        print(app_server_msg, file=sys.stderr)
        return 1

    skill_ok, skill_msg = _patch_skill_loader_target()
    if not skill_ok:
        print(skill_msg, file=sys.stderr)
        return 1

    print(f"{interactive_msg}; {system_msg}; {app_server_msg}; {skill_msg}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
