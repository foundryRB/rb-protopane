from __future__ import annotations

from pathlib import Path

from protopane.adapters.outbound.blocks.packaged_block_library import PackagedBlockLibrary
from protopane.adapters.outbound.design_systems.packaged_design_system_library import (
    PackagedDesignSystemLibrary,
)
from protopane.adapters.outbound.events import resolve_event_publisher
from protopane.adapters.outbound.notify.in_memory_project_change_broker import (
    InMemoryProjectChangeBroker,
)
from protopane.adapters.outbound.persistence.file_project_repository import FileProjectRepository
from protopane.adapters.outbound.persistence.file_template_repository import FileTemplateRepository
from protopane.application.ports.design_agent import DesignAgent
from protopane.application.ports.event_publisher import EventPublisher
from protopane.application.use_cases.archive_project import ArchiveProject
from protopane.application.use_cases.create_project import CreateProject
from protopane.application.use_cases.delete_project import DeleteProject
from protopane.application.use_cases.delete_scheme import DeleteScheme
from protopane.application.use_cases.delete_screen import DeleteScreen
from protopane.application.use_cases.delete_template import DeleteTemplate
from protopane.application.use_cases.export_project import ExportProject
from protopane.application.use_cases.get_design_system import GetDesignSystem
from protopane.application.use_cases.get_identity_source import GetIdentitySource
from protopane.application.use_cases.get_project import GetProject
from protopane.application.use_cases.get_template import GetTemplate
from protopane.application.use_cases.list_blocks import ListBlocks
from protopane.application.use_cases.list_design_systems import ListDesignSystems
from protopane.application.use_cases.list_identity_sources import ListIdentitySources
from protopane.application.use_cases.list_projects import ListProjects
from protopane.application.use_cases.list_templates import ListTemplates
from protopane.application.use_cases.rename_project import RenameProject
from protopane.application.use_cases.save_scheme import SaveScheme
from protopane.application.use_cases.save_screen import SaveScreen
from protopane.application.use_cases.save_template import SaveTemplate
from protopane.application.use_cases.save_theme import SaveTheme
from protopane.application.use_cases.unarchive_project import UnarchiveProject


class Container:
    """Composition root: builds the adapters and wires every use case to them.

    The container also decides capabilities: the design agent exists only when the
    composition enables it (the `agent` extra is installed and the operator opted
    in), and the adapters that expose it check `agent_enabled` rather than the
    environment.
    """

    def __init__(
        self,
        projects_dir: Path,
        templates_dir: Path,
        agent_enabled: bool = False,
        events: EventPublisher | None = None,
    ) -> None:
        repository = FileProjectRepository(projects_dir)
        templates = FileTemplateRepository(templates_dir)
        self.changes = InMemoryProjectChangeBroker()
        # The event bus this hub's grant reached, or the logging publisher when there
        # is none; either way every act completes unchanged (REF-Events).
        self.events: EventPublisher = events or resolve_event_publisher()
        self.list_projects = ListProjects(repository)
        self.create_project = CreateProject(repository, templates, self.events)
        self.get_project = GetProject(repository)
        self.delete_project = DeleteProject(repository, self.events)
        self.rename_project = RenameProject(repository, self.events)
        self.archive_project = ArchiveProject(repository, self.events)
        self.unarchive_project = UnarchiveProject(repository, self.events)
        design_system_library = PackagedDesignSystemLibrary()
        self.list_identity_sources = ListIdentitySources(design_system_library)
        self.get_identity_source = GetIdentitySource(design_system_library)
        self.save_theme = SaveTheme(repository, self.changes, design_system_library, self.events)
        self.save_scheme = SaveScheme(repository, self.changes, self.events)
        self.delete_scheme = DeleteScheme(repository, self.changes, self.events)
        self.save_screen = SaveScreen(repository, self.changes, self.events)
        self.delete_screen = DeleteScreen(repository, self.changes, self.events)
        self.export_project = ExportProject(repository, self.events)
        self.list_templates = ListTemplates(templates)
        self.get_template = GetTemplate(templates)
        self.save_template = SaveTemplate(templates)
        self.delete_template = DeleteTemplate(templates)
        self.list_blocks = ListBlocks(PackagedBlockLibrary())
        self.list_design_systems = ListDesignSystems(design_system_library)
        self.get_design_system = GetDesignSystem(design_system_library)
        self.agent_enabled = agent_enabled
        self.design_agent: DesignAgent | None = None
        if agent_enabled:
            # Imported lazily: claude-agent-sdk is an optional extra, absent on the
            # public hub image.
            from protopane.adapters.outbound.agent.claude_agent_design_agent import (
                ClaudeAgentDesignAgent,
            )

            self.design_agent = ClaudeAgentDesignAgent(
                self.get_project, self.save_screen, self.save_theme
            )
