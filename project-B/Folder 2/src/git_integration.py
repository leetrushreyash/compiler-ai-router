"""Git integration — scan repository history and track code smell evolution."""
from typing import Dict, List, Any, Optional
from pathlib import Path
from datetime import datetime
import json
import tempfile
import os


class GitAnalyzer:
    """Analyze code smells across Git commit history."""

    def __init__(self, repo_path: str = "."):
        """
        Args:
            repo_path: Path to a local Git repository
        """
        self.repo_path = Path(repo_path).resolve()
        self._repo = None

    # ------------------------------------------------------------------
    # Repository access (lazy-loaded)
    # ------------------------------------------------------------------
    @property
    def repo(self):
        if self._repo is None:
            try:
                from git import Repo
                self._repo = Repo(str(self.repo_path))
            except Exception as e:
                raise RuntimeError(
                    f"Cannot open Git repository at {self.repo_path}: {e}\n"
                    "Make sure gitpython is installed (pip install gitpython) "
                    "and the path points to a valid Git repo."
                )
        return self._repo

    # ------------------------------------------------------------------
    # Gather commits
    # ------------------------------------------------------------------
    def get_commits(
        self, branch: str = "HEAD", max_count: int = 50
    ) -> List[Dict[str, Any]]:
        """Return recent commits (newest first).

        Args:
            branch: Branch or ref to start from
            max_count: Maximum commits to retrieve

        Returns:
            List of commit dicts with hash, message, author, date
        """
        commits = []
        for c in self.repo.iter_commits(branch, max_count=max_count):
            commits.append({
                "hash": c.hexsha[:8],
                "hash_full": c.hexsha,
                "message": c.message.strip().split("\n")[0],
                "author": str(c.author),
                "date": datetime.fromtimestamp(c.committed_date).isoformat(),
                "timestamp": c.committed_date,
            })
        return commits

    # ------------------------------------------------------------------
    # Scan a single commit (checkout files into temp dir, analyse them)
    # ------------------------------------------------------------------
    def _get_python_files_at_commit(self, commit_hash: str) -> Dict[str, str]:
        """Retrieve all Python file contents at a given commit.

        Returns:
            dict mapping relative path → file content
        """
        commit = self.repo.commit(commit_hash)
        files: Dict[str, str] = {}

        def walk_tree(tree, prefix=""):
            for blob in tree.blobs:
                fpath = f"{prefix}{blob.name}" if not prefix else f"{prefix}/{blob.name}"
                if fpath.endswith(".py"):
                    try:
                        files[fpath] = blob.data_stream.read().decode("utf-8", errors="ignore")
                    except Exception:
                        pass
            for subtree in tree.trees:
                sub_prefix = f"{prefix}/{subtree.name}" if prefix else subtree.name
                walk_tree(subtree, sub_prefix)

        walk_tree(commit.tree)
        return files

    def scan_commit(self, commit_hash: str) -> Dict[str, Any]:
        """Run the smell detector on all Python files at a commit.

        Returns:
            Dict with commit info and list of detected issues
        """
        from ..rules.rule_engine import RuleEngine

        engine = RuleEngine()
        py_files = self._get_python_files_at_commit(commit_hash)

        all_issues: List[Dict[str, Any]] = []
        for fpath, content in py_files.items():
            issues = engine.apply_rules(content, fpath)
            all_issues.extend(issues)

        severity_counts = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}
        type_counts: Dict[str, int] = {}
        for issue in all_issues:
            sev = issue.get("severity", "MEDIUM")
            if sev in severity_counts:
                severity_counts[sev] += 1
            t = issue.get("type", "unknown")
            type_counts[t] = type_counts.get(t, 0) + 1

        return {
            "commit": commit_hash,
            "files_scanned": len(py_files),
            "total_issues": len(all_issues),
            "severity_counts": severity_counts,
            "type_counts": type_counts,
            "issues": all_issues,
        }

    # ------------------------------------------------------------------
    # Full timeline scan
    # ------------------------------------------------------------------
    def scan_history(
        self,
        branch: str = "HEAD",
        max_commits: int = 20,
        verbose: bool = False,
    ) -> Dict[str, Any]:
        """Scan multiple commits and build a timeline of code smells.

        Args:
            branch: Git branch / ref
            max_commits: How many recent commits to scan
            verbose: Print progress

        Returns:
            Dict with timeline data suitable for plotting
        """
        commits = self.get_commits(branch, max_commits)
        # Process from oldest to newest for a natural timeline
        commits = list(reversed(commits))

        timeline: List[Dict[str, Any]] = []

        for idx, commit_info in enumerate(commits):
            if verbose:
                print(
                    f"  [{idx + 1}/{len(commits)}] Scanning {commit_info['hash']} "
                    f"— {commit_info['message'][:50]}"
                )
            try:
                scan = self.scan_commit(commit_info["hash_full"])
                entry = {
                    **commit_info,
                    "files_scanned": scan["files_scanned"],
                    "total_issues": scan["total_issues"],
                    "severity_counts": scan["severity_counts"],
                    "type_counts": scan["type_counts"],
                }
                timeline.append(entry)
            except Exception as e:
                timeline.append({**commit_info, "error": str(e)})

        return {
            "repository": str(self.repo_path),
            "branch": branch,
            "commits_scanned": len(timeline),
            "timeline": timeline,
        }

    # ------------------------------------------------------------------
    # Visualise timeline
    # ------------------------------------------------------------------
    def plot_timeline(
        self,
        timeline_data: Dict[str, Any],
        output_dir: str = "data/evaluation",
        filename: str = "smell_timeline.png",
    ) -> str:
        """Plot code-smell count over commit history.

        Returns:
            Path to the saved PNG image
        """
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        entries = [e for e in timeline_data.get("timeline", []) if "error" not in e]
        if not entries:
            return ""

        labels = [e["hash"] for e in entries]
        total = [e["total_issues"] for e in entries]
        high = [e["severity_counts"].get("HIGH", 0) for e in entries]
        medium = [e["severity_counts"].get("MEDIUM", 0) for e in entries]
        low = [e["severity_counts"].get("LOW", 0) for e in entries]

        x = range(len(labels))

        fig, ax = plt.subplots(figsize=(max(10, len(labels) * 0.7), 6))

        ax.bar(x, high, label="HIGH", color="#d32f2f")
        ax.bar(x, medium, bottom=high, label="MEDIUM", color="#f57c00")
        low_bottom = [h + m for h, m in zip(high, medium)]
        ax.bar(x, low, bottom=low_bottom, label="LOW", color="#388e3c")

        ax.set_xticks(x)
        ax.set_xticklabels(labels, rotation=45, ha="right", fontsize=8)
        ax.set_xlabel("Commit")
        ax.set_ylabel("Issues Count")
        ax.set_title(f"Code Smell Evolution — {timeline_data.get('repository', '')}")
        ax.legend()
        plt.tight_layout()

        out_dir = Path(output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / filename
        fig.savefig(str(out_path), dpi=150)
        plt.close(fig)
        return str(out_path)

    def plot_smell_types_timeline(
        self,
        timeline_data: Dict[str, Any],
        output_dir: str = "data/evaluation",
        filename: str = "smell_types_timeline.png",
    ) -> str:
        """Plot per-smell-type counts over time.

        Returns:
            Path to saved image
        """
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        entries = [e for e in timeline_data.get("timeline", []) if "error" not in e]
        if not entries:
            return ""

        # Collect all smell types
        all_types: set = set()
        for e in entries:
            all_types.update(e.get("type_counts", {}).keys())
        all_types_sorted = sorted(all_types)

        labels = [e["hash"] for e in entries]
        x = range(len(labels))

        fig, ax = plt.subplots(figsize=(max(10, len(labels) * 0.7), 6))

        for stype in all_types_sorted:
            values = [e.get("type_counts", {}).get(stype, 0) for e in entries]
            ax.plot(x, values, marker="o", label=stype, linewidth=2)

        ax.set_xticks(x)
        ax.set_xticklabels(labels, rotation=45, ha="right", fontsize=8)
        ax.set_xlabel("Commit")
        ax.set_ylabel("Count")
        ax.set_title("Smell Types Over Time")
        ax.legend(loc="upper left", fontsize=7)
        plt.tight_layout()

        out_dir = Path(output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / filename
        fig.savefig(str(out_path), dpi=150)
        plt.close(fig)
        return str(out_path)

    # ------------------------------------------------------------------
    # Save timeline JSON
    # ------------------------------------------------------------------
    def save_timeline(
        self,
        timeline_data: Dict[str, Any],
        output_dir: str = "data/evaluation",
        filename: str = "smell_timeline.json",
    ) -> str:
        out_dir = Path(output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / filename
        with open(out_path, "w") as f:
            json.dump(timeline_data, f, indent=2, default=str)
        return str(out_path)
