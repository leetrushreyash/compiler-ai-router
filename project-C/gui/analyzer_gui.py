import tkinter as tk
from tkinter import filedialog, ttk, font
import threading
import json
import sys
import os

# ── Make sure imports resolve when running from any directory ──────────────────
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)
sys.path.insert(0, os.path.join(parent_dir, 'codes'))
from unified_analyzer import analyze_file

# ── Colour Palette ─────────────────────────────────────────────────────────────
BG          = "#0f0f1a"
PANEL       = "#1a1a2e"
CARD        = "#16213e"
ACCENT      = "#7c3aed"
ACCENT2     = "#a855f7"
TEXT        = "#e2e8f0"
MUTED       = "#94a3b8"
SUCCESS     = "#22c55e"
WARNING     = "#f59e0b"
DANGER      = "#ef4444"
BORDER      = "#2d2d4e"

# ── Main Application ───────────────────────────────────────────────────────────
class AnalyzerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("AST C++ Static Analyzer")
        self.geometry("1080x720")
        self.minsize(900, 600)
        self.configure(bg=BG)
        self._build_ui()

    # ── UI Construction ──────────────────────────────────────────────────────
    def _build_ui(self):
        # ---- Header ----
        header = tk.Frame(self, bg=PANEL, pady=14)
        header.pack(fill="x")

        tk.Label(header, text="⚡ AST C++ Static Analyzer",
                 bg=PANEL, fg=TEXT,
                 font=("Segoe UI", 18, "bold")).pack(side="left", padx=24)

        tk.Label(header, text="Code Smell & Security Vulnerability Detector",
                 bg=PANEL, fg=MUTED,
                 font=("Segoe UI", 10)).pack(side="left", padx=4)

        # ---- File Picker Row ----
        row = tk.Frame(self, bg=BG, pady=16)
        row.pack(fill="x", padx=24)

        self.file_var = tk.StringVar(value="No file selected…")
        tk.Label(row, textvariable=self.file_var, bg=BG, fg=MUTED,
                 font=("Segoe UI", 10), anchor="w",
                 wraplength=700).pack(side="left", fill="x", expand=True)

        tk.Button(row, text="📂  Browse .cpp File",
                  bg=ACCENT, fg="white", activebackground=ACCENT2,
                  activeforeground="white",
                  font=("Segoe UI", 10, "bold"),
                  relief="flat", padx=14, pady=8, cursor="hand2",
                  command=self._browse).pack(side="right", padx=(12, 0))

        tk.Button(row, text="▶  Analyze",
                  bg=SUCCESS, fg="white", activebackground="#16a34a",
                  activeforeground="white",
                  font=("Segoe UI", 10, "bold"),
                  relief="flat", padx=18, pady=8, cursor="hand2",
                  command=self._run_analysis).pack(side="right")

        # ---- Status bar ----
        self.status_var = tk.StringVar(value="Ready. Select a C++ file and click Analyze.")
        status_bar = tk.Frame(self, bg=PANEL, pady=6)
        status_bar.pack(fill="x")
        tk.Label(status_bar, textvariable=self.status_var,
                 bg=PANEL, fg=MUTED,
                 font=("Segoe UI", 9), anchor="w").pack(side="left", padx=16)

        self.progress = ttk.Progressbar(status_bar, mode="indeterminate", length=150)
        self.progress.pack(side="right", padx=16)

        # ---- Separator ----
        tk.Frame(self, bg=BORDER, height=1).pack(fill="x")

        # ---- Results Area ----
        results_frame = tk.Frame(self, bg=BG)
        results_frame.pack(fill="both", expand=True, padx=24, pady=16)

        # Summary Cards Row
        self.cards_frame = tk.Frame(results_frame, bg=BG)
        self.cards_frame.pack(fill="x", pady=(0, 16))

        # Scrollable function list
        list_label = tk.Label(results_frame, text="Function Analysis",
                              bg=BG, fg=TEXT,
                              font=("Segoe UI", 12, "bold"))
        list_label.pack(anchor="w", pady=(0, 8))

        # Canvas + scrollbar for function cards
        canvas_frame = tk.Frame(results_frame, bg=BG)
        canvas_frame.pack(fill="both", expand=True)

        self.canvas = tk.Canvas(canvas_frame, bg=BG, bd=0, highlightthickness=0)
        scrollbar = ttk.Scrollbar(canvas_frame, orient="vertical",
                                  command=self.canvas.yview)
        self.scroll_frame = tk.Frame(self.canvas, bg=BG)

        self.scroll_frame.bind("<Configure>",
            lambda e: self.canvas.configure(
                scrollregion=self.canvas.bbox("all")))

        self.canvas.create_window((0, 0), window=self.scroll_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Mouse wheel
        self.canvas.bind_all("<MouseWheel>",
            lambda e: self.canvas.yview_scroll(-1*(e.delta//120), "units"))

        # Placeholder text
        self._show_placeholder()

    # ── Helpers ─────────────────────────────────────────────────────────────
    def _show_placeholder(self):
        for w in self.scroll_frame.winfo_children():
            w.destroy()
        tk.Label(self.scroll_frame,
                 text="🔍  Select a C++ file and click Analyze to see results here.",
                 bg=BG, fg=MUTED, font=("Segoe UI", 12)).pack(pady=40)

    def _clear_cards(self):
        for w in self.cards_frame.winfo_children():
            w.destroy()

    def _make_summary_card(self, parent, label, value, color):
        card = tk.Frame(parent, bg=CARD, padx=20, pady=14,
                        relief="flat", bd=0)
        card.pack(side="left", padx=(0, 12), fill="y")
        tk.Label(card, text=value, bg=CARD, fg=color,
                 font=("Segoe UI", 22, "bold")).pack()
        tk.Label(card, text=label, bg=CARD, fg=MUTED,
                 font=("Segoe UI", 9)).pack()

    def _severity_color(self, sev):
        return {
            "Critical": DANGER,
            "High":     DANGER,
            "Medium":   WARNING,
            "Low":      WARNING,
            "None":     SUCCESS,
        }.get(sev, MUTED)

    def _browse(self):
        path = filedialog.askopenfilename(
            title="Select a C++ File",
            filetypes=[("C++ Files", "*.cpp *.cc *.cxx *.h *.hpp"),
                       ("All Files", "*.*")])
        if path:
            self.file_var.set(path)
            self._show_placeholder()
            self._clear_cards()
            self.status_var.set("File selected. Click Analyze.")

    def _run_analysis(self):
        path = self.file_var.get()
        if path == "No file selected…" or not os.path.isfile(path):
            self.status_var.set("⚠  Please select a valid .cpp file first.")
            return

        self.status_var.set("Analyzing… please wait.")
        self.progress.start(10)
        self._show_placeholder()
        self._clear_cards()

        thread = threading.Thread(target=self._do_analysis, args=(path,), daemon=True)
        thread.start()

    def _do_analysis(self, path):
        try:
            result = analyze_file(path)
            self.after(0, self._render_results, result)
        except Exception as ex:
            self.after(0, self._render_error, str(ex))
        finally:
            self.after(0, self.progress.stop)

    # ── Rendering ────────────────────────────────────────────────────────────
    def _render_error(self, msg):
        self.status_var.set(f"Error: {msg}")
        for w in self.scroll_frame.winfo_children():
            w.destroy()
        tk.Label(self.scroll_frame, text=f"❌ {msg}",
                 bg=BG, fg=DANGER, font=("Segoe UI", 11),
                 wraplength=800, justify="left").pack(pady=20, anchor="w")

    def _render_results(self, result):
        if "error" in result:
            self._render_error(result["error"])
            return

        funcs = result.get("functions", [])
        self.status_var.set(
            f"✅  Analysis complete — {len(funcs)} function(s) found in "
            f"{os.path.basename(result['file'])}")

        # ── Summary Cards ──────────────────────────────────────────────────
        total      = len(funcs)
        smelly     = sum(1 for f in funcs if f["code_smell"]["is_smelly"])
        vulnerable = sum(1 for f in funcs if f["security"]["has_vulnerabilities"])
        clean      = total - smelly - vulnerable

        self._make_summary_card(self.cards_frame, "Total Functions", str(total),  TEXT)
        self._make_summary_card(self.cards_frame, "Code Smells",     str(smelly),    WARNING)
        self._make_summary_card(self.cards_frame, "Security Risks",  str(vulnerable), DANGER)
        self._make_summary_card(self.cards_frame, "Clean Functions", str(max(0,clean)), SUCCESS)

        # ── Function Cards ─────────────────────────────────────────────────
        for w in self.scroll_frame.winfo_children():
            w.destroy()

        if not funcs:
            tk.Label(self.scroll_frame,
                     text="No functions found in this file.",
                     bg=BG, fg=MUTED, font=("Segoe UI", 11)).pack(pady=20)
            return

        for func in funcs:
            self._render_function_card(func)

    def _render_function_card(self, func):
        sev   = func["overall_severity"]
        sev_c = self._severity_color(sev)

        # Outer card
        card = tk.Frame(self.scroll_frame, bg=CARD, pady=0,
                        relief="flat", bd=0)
        card.pack(fill="x", pady=6, padx=2)

        # Left accent bar
        accent_bar = tk.Frame(card, bg=sev_c, width=5)
        accent_bar.pack(side="left", fill="y")

        inner = tk.Frame(card, bg=CARD, padx=16, pady=12)
        inner.pack(side="left", fill="both", expand=True)

        # ── Header row ──────────────────────────────────────────────────
        header = tk.Frame(inner, bg=CARD)
        header.pack(fill="x")

        icon = "⚠️" if func["code_smell"]["is_smelly"] else "🛡️"
        if func["security"]["has_vulnerabilities"]:
            icon = "🚨"

        tk.Label(header, text=f"{icon}  {func['name']}",
                 bg=CARD, fg=TEXT,
                 font=("Segoe UI", 12, "bold")).pack(side="left")

        sev_badge = tk.Label(header,
                             text=f"  {sev}  ",
                             bg=sev_c, fg="white",
                             font=("Segoe UI", 9, "bold"),
                             padx=6, pady=2)
        sev_badge.pack(side="right")

        tk.Label(header, text=f"Line {func['line'] + 1}",
                 bg=CARD, fg=MUTED,
                 font=("Segoe UI", 9)).pack(side="right", padx=12)

        # ── Code Smell Details ───────────────────────────────────────────
        smell = func["code_smell"]
        smell_color = WARNING if smell["is_smelly"] else SUCCESS
        smell_text  = f"{'🟡 ' + smell['classification'] if smell['is_smelly'] else '✅ Clean Code'}  " \
                      f"(Confidence: {smell['probability_score']}%)"

        tk.Label(inner, text=smell_text,
                 bg=CARD, fg=smell_color,
                 font=("Segoe UI", 10)).pack(anchor="w", pady=(6, 2))

        m = smell["metrics"]
        metrics_text = (f"AST Nodes: {m['total_ast_nodes']}   |   "
                        f"Max Depth: {m['max_depth']}   |   "
                        f"If Branches: {m['if_count']}   |   "
                        f"Loops: {m['loop_count']}")
        tk.Label(inner, text=metrics_text,
                 bg=CARD, fg=MUTED,
                 font=("Segoe UI", 9)).pack(anchor="w")

        # ── Security Issues ──────────────────────────────────────────────
        if func["security"]["has_vulnerabilities"]:
            tk.Frame(inner, bg=BORDER, height=1).pack(fill="x", pady=8)
            for issue in func["security"]["issues"]:
                row = tk.Frame(inner, bg=CARD)
                row.pack(fill="x", pady=1)
                tk.Label(row, text="🔴",
                         bg=CARD, fg=DANGER,
                         font=("Segoe UI", 10)).pack(side="left")
                tk.Label(row, text=f"[Line {issue['line'] + 1}]  {issue['message']}",
                         bg=CARD, fg=DANGER,
                         font=("Segoe UI", 10),
                         wraplength=800, justify="left").pack(side="left", padx=6)

# ── Entry Point ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = AnalyzerApp()
    app.mainloop()
