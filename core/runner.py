"""Claude CLI Runner pour exécution parallèle en mode headless."""

import asyncio
import json
import subprocess
from pathlib import Path
from typing import Optional, List, Callable, Dict, Any
from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class ClaudeResult:
    """Résultat d'une exécution Claude.

    Attributes:
        feature_id: Identifiant de la feature
        success: True si l'exécution a réussi
        result: Texte de la réponse Claude
        cost_usd: Coût en USD
        duration_ms: Durée en millisecondes
        session_id: ID de session pour reprise éventuelle
        error: Message d'erreur si échec
        started_at: Date/heure de début
        finished_at: Date/heure de fin
        num_turns: Nombre de tours de conversation
    """
    feature_id: str
    success: bool
    result: str
    cost_usd: float
    duration_ms: int
    session_id: str
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    num_turns: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convertit en dictionnaire (pour sérialisation JSON)."""
        data = asdict(self)
        # Convertir les datetime en ISO format
        if self.started_at:
            data["started_at"] = self.started_at.isoformat()
        if self.finished_at:
            data["finished_at"] = self.finished_at.isoformat()
        return data


class ClaudeRunner:
    """Exécute Claude Code en mode headless de manière asynchrone.

    Permet l'exécution parallèle de plusieurs instances de Claude Code
    avec contrôle du nombre maximum d'exécutions simultanées via Semaphore.

    Attributes:
        max_parallel: Nombre max d'exécutions parallèles
        permission_mode: Mode de permissions Claude Code
        allowed_tools: Liste des outils autorisés
        timeout_seconds: Timeout par exécution
        semaphore: Semaphore asyncio pour limiter le parallélisme

    Example:
        >>> runner = ClaudeRunner(max_parallel=3)
        >>> result = await runner.run_single(
        ...     worktree_path=Path("/path/to/worktree"),
        ...     prompt="Implement feature X",
        ...     feature_id="feature-x"
        ... )
    """

    DEFAULT_ALLOWED_TOOLS = [
        "Read", "Write", "Edit", "Glob", "Grep",
        "Bash(npm test)", "Bash(npm run lint)",
        "Bash(bundle exec rspec)", "Bash(bundle exec rubocop)",
        "Bash(pytest)", "Bash(python -m pytest)"
    ]

    def __init__(
        self,
        max_parallel: int = 3,
        permission_mode: str = "acceptEdits",
        allowed_tools: Optional[List[str]] = None,
        timeout_seconds: int = 1800,  # 30 min par défaut
        claude_binary: str = "claude"
    ):
        """Initialise le runner.

        Args:
            max_parallel: Nombre max d'exécutions simultanées
            permission_mode: Mode permissions ("acceptEdits", "askUser", etc.)
            allowed_tools: Liste des outils autorisés (None = défaut)
            timeout_seconds: Timeout par feature en secondes
            claude_binary: Chemin vers le binaire claude (défaut: "claude" dans PATH)
        """
        self.max_parallel = max_parallel
        self.permission_mode = permission_mode
        self.allowed_tools = allowed_tools or self.DEFAULT_ALLOWED_TOOLS
        self.timeout_seconds = timeout_seconds
        self.claude_binary = claude_binary
        self.semaphore = asyncio.Semaphore(max_parallel)

    async def run_single(
        self,
        worktree_path: Path,
        prompt: str,
        feature_id: str,
        session_id: Optional[str] = None,
        append_system_prompt: Optional[str] = None
    ) -> ClaudeResult:
        """Lance Claude Code sur un worktree de manière asynchrone.

        Args:
            worktree_path: Chemin vers le worktree
            prompt: Prompt à envoyer à Claude
            feature_id: ID de la feature
            session_id: ID de session pour reprendre (optionnel)
            append_system_prompt: Contexte additionnel à ajouter (optionnel)

        Returns:
            ClaudeResult avec le résultat de l'exécution
        """
        started_at = datetime.now()

        # Construire la commande
        cmd = [
            self.claude_binary,
            "-p", prompt,
            "--output-format", "json",
            "--permission-mode", self.permission_mode,
            "--allowedTools", ",".join(self.allowed_tools)
        ]

        if session_id:
            cmd.extend(["--resume", session_id])

        if append_system_prompt:
            cmd.extend(["--append-system-prompt", append_system_prompt])

        try:
            # Lancer le processus de manière asynchrone
            process = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=worktree_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            # Attendre la fin avec timeout
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=self.timeout_seconds
            )

            finished_at = datetime.now()

            # Gérer les erreurs de processus
            if process.returncode != 0:
                return ClaudeResult(
                    feature_id=feature_id,
                    success=False,
                    result="",
                    cost_usd=0.0,
                    duration_ms=0,
                    session_id="",
                    error=stderr.decode().strip() or "Process returned non-zero exit code",
                    started_at=started_at,
                    finished_at=finished_at
                )

            # Parser le JSON output
            try:
                result_json = json.loads(stdout.decode())
            except json.JSONDecodeError as e:
                return ClaudeResult(
                    feature_id=feature_id,
                    success=False,
                    result=stdout.decode()[:500],  # Premiers 500 chars
                    cost_usd=0.0,
                    duration_ms=0,
                    session_id="",
                    error=f"JSON parse error: {e}",
                    started_at=started_at,
                    finished_at=finished_at
                )

            # Construire le résultat
            return ClaudeResult(
                feature_id=feature_id,
                success=result_json.get("subtype") == "success",
                result=result_json.get("result", ""),
                cost_usd=result_json.get("total_cost_usd", 0.0),
                duration_ms=result_json.get("duration_ms", 0),
                session_id=result_json.get("session_id", ""),
                started_at=started_at,
                finished_at=finished_at,
                num_turns=result_json.get("num_turns", 0)
            )

        except asyncio.TimeoutError:
            finished_at = datetime.now()
            return ClaudeResult(
                feature_id=feature_id,
                success=False,
                result="",
                cost_usd=0.0,
                duration_ms=self.timeout_seconds * 1000,
                session_id="",
                error=f"Timeout après {self.timeout_seconds}s",
                started_at=started_at,
                finished_at=finished_at
            )

        except FileNotFoundError:
            finished_at = datetime.now()
            return ClaudeResult(
                feature_id=feature_id,
                success=False,
                result="",
                cost_usd=0.0,
                duration_ms=0,
                session_id="",
                error=f"Claude binary '{self.claude_binary}' not found in PATH",
                started_at=started_at,
                finished_at=finished_at
            )

        except Exception as e:
            finished_at = datetime.now()
            return ClaudeResult(
                feature_id=feature_id,
                success=False,
                result="",
                cost_usd=0.0,
                duration_ms=0,
                session_id="",
                error=f"Unexpected error: {type(e).__name__}: {e}",
                started_at=started_at,
                finished_at=finished_at
            )

    async def run_wave(
        self,
        tasks: List[tuple],  # (worktree_path, prompt, feature_id)
        on_progress: Optional[Callable[[str, str], None]] = None
    ) -> List[ClaudeResult]:
        """Exécute une vague de features en parallèle.

        Utilise un semaphore pour limiter le nombre d'exécutions simultanées.

        Args:
            tasks: Liste de tuples (worktree_path, prompt, feature_id)
            on_progress: Callback optionnel pour suivi de progression
                        Signature: (feature_id: str, status: str) -> None
                        Status: "started", "completed", "failed"

        Returns:
            Liste des ClaudeResult pour chaque task

        Example:
            >>> tasks = [
            ...     (Path("/wt/auth"), "Implement auth", "auth"),
            ...     (Path("/wt/api"), "Implement API", "api")
            ... ]
            >>> results = await runner.run_wave(tasks)
        """

        async def run_with_semaphore(worktree_path, prompt, feature_id):
            """Exécute une task avec le semaphore."""
            async with self.semaphore:
                if on_progress:
                    on_progress(feature_id, "started")

                result = await self.run_single(worktree_path, prompt, feature_id)

                if on_progress:
                    status = "completed" if result.success else "failed"
                    on_progress(feature_id, status)

                return result

        # Créer les coroutines pour toutes les tasks
        coroutines = [
            run_with_semaphore(wt, prompt, fid)
            for wt, prompt, fid in tasks
        ]

        # Exécuter en parallèle avec gather
        return await asyncio.gather(*coroutines)

    async def run_sequential(
        self,
        tasks: List[tuple],  # (worktree_path, prompt, feature_id)
        on_progress: Optional[Callable[[str, str], None]] = None
    ) -> List[ClaudeResult]:
        """Exécute une liste de tasks de manière séquentielle.

        Utile pour debugging ou quand le parallélisme n'est pas souhaité.

        Args:
            tasks: Liste de tuples (worktree_path, prompt, feature_id)
            on_progress: Callback optionnel pour suivi de progression

        Returns:
            Liste des ClaudeResult dans l'ordre des tasks
        """
        results = []

        for worktree_path, prompt, feature_id in tasks:
            if on_progress:
                on_progress(feature_id, "started")

            result = await self.run_single(worktree_path, prompt, feature_id)

            if on_progress:
                status = "completed" if result.success else "failed"
                on_progress(feature_id, status)

            results.append(result)

        return results

    def check_claude_available(self) -> bool:
        """Vérifie que le binaire Claude est disponible.

        Returns:
            True si Claude est dans le PATH et exécutable
        """
        try:
            result = subprocess.run(
                [self.claude_binary, "--version"],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def get_claude_version(self) -> Optional[str]:
        """Récupère la version de Claude Code installée.

        Returns:
            Version string ou None si indisponible
        """
        try:
            result = subprocess.run(
                [self.claude_binary, "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
        return None
