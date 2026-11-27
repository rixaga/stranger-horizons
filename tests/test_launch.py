"""Background-Blender launch command from launch_args.json (list = run_shot args, dict = any script)."""
from pathlib import Path


def test_list_spec_runs_run_shot():
    from sh_launch import build_command
    here = Path("/ep/blender/scripts")
    cmd = build_command("/B", here, ["--scene", "S022"])
    assert cmd == ["/B", "--background", "--factory-startup", "--python", str(here / "run_shot.py"), "--", "--scene", "S022"]


def test_dict_spec_runs_named_script_relative_to_the_episode():
    from sh_launch import build_command
    here = Path("/ep/blender/scripts")
    cmd = build_command("/B", here, {"script": "shorts/mockup/toon_mockup.py", "args": ["--percent", "50"]})
    assert cmd[4] == str(Path("/ep/shorts/mockup/toon_mockup.py"))
    assert cmd[-2:] == ["--percent", "50"]
