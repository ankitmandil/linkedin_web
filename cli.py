import argparse
import sys
import json
import csv
from pathlib import Path

# Ensure UTF-8 output on Windows terminal
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from core.orchestrator import ProductHiringManagerSystem
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console(highlight=False)

def run_cli():
    parser = argparse.ArgumentParser(
        description="AI System to Find Similar/Higher Roles and Executive Hiring Manager Profiles"
    )
    parser.add_argument(
        "--resume",
        type=str,
        default="sample_resumes/twisha_prasad.txt",
        help="Path to resume file (default: sample_resumes/twisha_prasad.txt)"
    )
    parser.add_argument(
        "--level",
        type=str,
        choices=["all", "higher", "similar"],
        default="all",
        help="Filter role level: 'higher', 'similar', or 'all'"
    )
    parser.add_argument(
        "--location",
        type=str,
        default="Bengaluru, Karnataka, India",
        help="Location to search (default: Bengaluru, Karnataka, India)"
    )
    parser.add_argument(
        "--page",
        type=int,
        default=1,
        help="Page number for pagination (default: 1)"
    )
    parser.add_argument(
        "--page-size",
        "--limit",
        dest="page_size",
        type=int,
        default=5,
        help="Results per page / limit (default: 5)"
    )
    parser.add_argument(
        "--sort",
        type=str,
        choices=["date", "match"],
        default="date",
        help="Sort order: 'date' (latest posted first, default) or 'match' (highest score first)"
    )
    parser.add_argument(
        "--export-json",
        type=str,
        default="",
        help="Export results to JSON file path"
    )
    parser.add_argument(
        "--export-csv",
        type=str,
        default="",
        help="Export results to CSV file path"
    )

    args = parser.parse_args()

    resume_path = Path(args.resume)
    if not resume_path.exists():
        console.print(f"[bold red]Error: Resume file '{args.resume}' does not exist![/bold red]")
        sys.exit(1)

    resume_text = resume_path.read_text(encoding="utf-8")

    console.print(Panel.fit(
        "[bold cyan]AI LinkedIn Executive Role & Hiring Manager Finder[/bold cyan]\n"
        "[dim]Dynamic Career Track Analysis • Deep Resume vs JD NLP Matching • Verified Leadership Discovery[/dim]",
        border_style="cyan"
    ))

    system = ProductHiringManagerSystem()

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("[yellow]Initializing analysis...", total=None)

        def update_progress(msg: str):
            progress.update(task, description=f"[bold green]{msg}[/bold green]")

        data = system.run(
            resume_text=resume_text,
            level_filter=args.level,
            location=args.location,
            page=args.page,
            page_size=args.page_size,
            sort_by=args.sort,
            progress_callback=update_progress
        )

    cand = data["candidate"]
    opps = data["opportunities"]

    # Candidate Summary Panel
    candidate_summary = (
        f"[bold]Candidate:[/bold] [green]{cand['name']}[/green] | [bold]Track:[/bold] [magenta]{cand['track'].replace('_', ' ')}[/magenta] | [bold]YoE:[/bold] [yellow]{cand['years_of_experience']:.0f}+ Years[/yellow]\n"
        f"[bold]Current Seniority:[/bold] {cand['current_title']} @ {cand['current_company']}\n"
        f"[bold]Identified Higher Roles:[/bold] {', '.join(cand['target_higher_roles'][:3])}\n"
        f"[bold]Identified Similar Roles:[/bold] {', '.join(cand['target_similar_roles'][:2])}\n"
        f"[bold]Core Domains / Skills:[/bold] {', '.join((cand['core_domains'] + cand['skills'])[:5])}"
    )
    console.print(Panel(candidate_summary, title="[bold white]Candidate Seniority & Track Profile[/bold white]", border_style="green"))

    # Results Table
    table = Table(title=f"Discovered Opportunities & Hiring Managers (Page {args.page} - {len(opps)} found)", show_lines=True)
    table.add_column("#", style="dim", width=3)
    table.add_column("Level", style="bold", width=14)
    table.add_column("Role & Company", width=30)
    table.add_column("JD Match", style="magenta", width=9)
    table.add_column("Matched Skills", style="green", width=22)
    table.add_column("Hiring Manager & Designation", style="cyan", width=30)
    table.add_column("LinkedIn Profile URL", style="blue", width=38)

    for idx, opp in enumerate(opps, 1):
        level_style = "[bold green][HIGHER ROLE][/bold green]" if opp["role_level_category"] == "Higher Role" else "[bold yellow][SIMILAR ROLE][/bold yellow]"
        
        hm = opp["hiring_manager"]
        hm_cell = f"[bold]{hm['name']}[/bold]\n[dim]{hm['title']}[/dim]"
        hm_url = hm["linkedin_url"]
        
        job_cell = f"[bold]{opp['job_title']}[/bold]\n[dim]{opp['company']} ({opp['location']})[/dim]\nJob: {opp['job_url']}"
        skills_cell = ", ".join(opp.get("matched_skills", [])[:4]) or "Domain fit"

        table.add_row(
            str(idx),
            level_style,
            job_cell,
            f"{opp['match_score']}%\n[dim]({opp['cosine_similarity_pct']}% sim)[/dim]",
            skills_cell,
            hm_cell,
            hm_url
        )

    console.print(table)

    # Detailed Outreach Sample for Top Result
    if opps:
        top = opps[0]
        outreach_panel = (
            f"[bold cyan]Role:[/bold cyan] {top['job_title']} @ {top['company']} ([bold]{top['role_level_category']}[/bold])\n"
            f"[bold cyan]Hiring Manager:[/bold cyan] {top['hiring_manager']['name']} ({top['hiring_manager']['title']})\n"
            f"[bold cyan]LinkedIn URL:[/bold cyan] {top['hiring_manager']['linkedin_url']}\n"
            f"[bold cyan]JD Match Breakdown:[/bold cyan]\n{top['match_rationale']}\n\n"
            f"[bold yellow]LinkedIn Connection Request Note (<300 chars):[/bold yellow]\n"
            f"\"{top['outreach']['connection_note']}\"\n\n"
            f"[bold yellow]Executive InMail Pitch:[/bold yellow]\n"
            f"{top['outreach']['inmail_pitch']}"
        )
        console.print(Panel(outreach_panel, title="[bold green]Sample AI Outreach & JD Match Analysis[/bold green]", border_style="magenta"))

    # Export to JSON
    if args.export_json:
        out_path = Path(args.export_json)
        out_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        console.print(f"[bold green]Results saved to JSON:[/bold green] {out_path.resolve()}")

    # Export to CSV
    if args.export_csv:
        csv_path = Path(args.export_csv)
        with open(csv_path, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                "Job Title", "Company", "Location", "Role Level", "Match Score", "Cosine Sim",
                "Job URL", "Hiring Manager Name", "Hiring Manager Title",
                "Hiring Manager LinkedIn URL", "Matched Skills", "Connection Note", "InMail Pitch"
            ])
            for o in opps:
                hm = o["hiring_manager"]
                out = o["outreach"]
                writer.writerow([
                    o["job_title"], o["company"], o["location"], o["role_level_category"],
                    f"{o['match_score']}%", f"{o['cosine_similarity_pct']}%", o["job_url"],
                    hm["name"], hm["title"], hm["linkedin_url"],
                    ", ".join(o.get("matched_skills", [])), out["connection_note"], out["inmail_pitch"]
                ])
        console.print(f"[bold green]Results saved to CSV:[/bold green] {csv_path.resolve()}")

if __name__ == "__main__":
    run_cli()
