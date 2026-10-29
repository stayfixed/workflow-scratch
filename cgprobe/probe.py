"""IS3 Task 12: does a cgroup v2 child end a descendant that left the process group?
Standard library only. Prints every step's result and exits 0 whatever it found."""
import os, signal, subprocess, sys, time
from pathlib import Path

def say(*a): print("probe:", *a, flush=True)

try:
    line = Path("/proc/self/cgroup").read_text().strip().splitlines()
    say("/proc/self/cgroup:", line)
    rel = next((l.split("::", 1)[1] for l in line if l.startswith("0::")), None)
except OSError as e:
    say("no /proc/self/cgroup:", e); sys.exit(0)
if rel is None:
    say("no cgroup v2 line (0::)"); sys.exit(0)
own = Path("/sys/fs/cgroup" + rel)
say("own cgroup:", own, "exists:", own.is_dir(), "writable:", os.access(own, os.W_OK),
    "has cgroup.kill:", (own / "cgroup.kill").exists())
try:
    say("subtree_control:", (own / "cgroup.subtree_control").read_text().strip() or "(empty)")
except OSError as e:
    say("subtree_control unreadable:", e)
child = own / f"probe-{os.getpid()}"
try:
    child.mkdir()
    say("child created:", child)
except OSError as e:
    say("child not created:", type(e).__name__, e); child = None

def enter():
    if child is not None:
        (child / "cgroup.procs").write_text("0")

try:
    proc = subprocess.Popen(["sh", "-c", "setsid sleep 300 >/dev/null 2>&1 & echo $!; sleep 1"],
                            stdout=subprocess.PIPE, text=True, start_new_session=True,
                            preexec_fn=enter if child is not None else None)
except Exception as e:  # preexec failure surfaces as SubprocessError
    say("Popen with the cgroup entry failed:", type(e).__name__, e)
    proc = subprocess.Popen(["sh", "-c", "setsid sleep 300 >/dev/null 2>&1 & echo $!; sleep 1"],
                            stdout=subprocess.PIPE, text=True, start_new_session=True)
    child = None
leaver = int(proc.stdout.readline().strip())
time.sleep(1)  # let the background child reach setsid() before the group is ended
def pgid(pid):
    try:
        return os.getpgid(pid)
    except ProcessLookupError:
        return None
say("command pid", proc.pid, "pgid", pgid(proc.pid), "setsid pid", leaver, "pgid", pgid(leaver), "left the group:", pgid(leaver) not in (None, proc.pid))
if child is not None:
    say("child cgroup.procs:", (child / "cgroup.procs").read_text().split())
# End the command's process group as stayfixed.processes.kill_group does: TERM, then KILL.
try:
    os.killpg(proc.pid, signal.SIGTERM)
    try:
        proc.wait(5)
    except subprocess.TimeoutExpired:
        os.killpg(proc.pid, signal.SIGKILL); proc.wait()
except ProcessLookupError:
    pass
def alive(pid):
    try:
        os.kill(pid, 0); return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
say("after the group kill, setsid pid alive:", alive(leaver))
if child is not None:
    try:
        (child / "cgroup.kill").write_text("1")
        say("wrote 1 to cgroup.kill")
        deadline = time.monotonic() + 5
        populated = None
        while time.monotonic() < deadline:
            populated = (child / "cgroup.events").read_text()
            if "populated 0" in populated:
                break
            time.sleep(0.1)
        say("cgroup.events:", " ".join(populated.split()) if populated else None)
    except OSError as e:
        say("cgroup.kill failed:", type(e).__name__, e)
    say("after cgroup.kill, setsid pid alive:", alive(leaver))
    try:
        child.rmdir(); say("child removed")
    except OSError as e:
        say("child not removed:", type(e).__name__, e)
if alive(leaver):
    try:
        os.kill(leaver, signal.SIGKILL)
    except OSError:
        pass
say("done")
