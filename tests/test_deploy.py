import subprocess

import pytest

from agentops import DeployRefused, assert_preview_only, build_bundle, publish


def fake_run(calls):
    def run(argv, **kw):
        calls.append((argv, kw))
        return subprocess.CompletedProcess(argv, 0, "https://preview.example.test\n", "")
    return run


def test_clean_bundle_publishes_to_preview(tmp_path):
    src, out = tmp_path / "src", tmp_path / "out"
    src.mkdir()
    (src / "index.html").write_text("<h1>Revenue and lane volume</h1>")
    findings = build_bundle(src, out)
    assert findings == []
    assert (out / "robots.txt").read_text().startswith("User-agent: *")
    calls = []
    publish(out, findings, run=fake_run(calls))
    assert calls[0][0] == ["vercel", "deploy", "--yes"]


def test_dirty_bundle_is_refused_and_nothing_runs(tmp_path):
    src, out = tmp_path / "src", tmp_path / "out"
    src.mkdir()
    (src / "index.html").write_text("contact buyer@customer.example")
    findings = build_bundle(src, out)
    assert [f.rule for f in findings] == ["email"]
    calls = []
    with pytest.raises(DeployRefused, match="lint finding"):
        publish(out, findings, run=fake_run(calls))
    assert calls == []


@pytest.mark.parametrize("flag", ["--prod", "--production", "--target=production"])
def test_production_flags_are_rejected(flag):
    with pytest.raises(DeployRefused):
        assert_preview_only(["vercel", "deploy", flag])


def test_target_production_pair_is_rejected():
    with pytest.raises(DeployRefused):
        assert_preview_only(["vercel", "deploy", "--target", "production"])


def test_prod_cannot_be_smuggled_through_publish(tmp_path):
    calls = []
    with pytest.raises(DeployRefused):
        publish(tmp_path, [], argv=["vercel", "deploy", "--prod"], run=fake_run(calls))
    assert calls == []


def test_excluded_paths_never_reach_the_bundle(tmp_path):
    src, out = tmp_path / "src", tmp_path / "out"
    (src / "private").mkdir(parents=True)
    (src / "index.html").write_text("ok")
    (src / "private" / "notes.json").write_text("{}")
    build_bundle(src, out, exclude=["private"])
    assert not (out / "private").exists()
