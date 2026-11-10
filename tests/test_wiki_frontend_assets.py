"""Prevent a false-positive green deploy when Wiki loads HTML but no assets."""

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class WikiFrontendAssetsContract(unittest.TestCase):
    def test_docker_image_copies_built_wiki_public_folder_as_real_files(self):
        docker = (ROOT / "deploy" / "Dockerfile").read_text()
        self.assertIn("rm -rf assets/wiki", docker)
        self.assertIn("cp -a apps/wiki/wiki/public/. assets/wiki/", docker)
        self.assertIn("index-*.js", docker)
        self.assertIn("index-*.css", docker)

    def test_staging_and_production_verify_actual_wiki_bundles(self):
        script = ROOT / "deploy" / "scripts" / "check-wiki-assets.sh"
        source = script.read_text()
        self.assertIn("/wiki-app/spaces", source)
        self.assertIn("frontend/assets/", source)
        self.assertIn("content_type", source)
        smoke = (ROOT / "deploy" / "scripts" / "smoke-site.sh").read_text()
        self.assertIn("bash scripts/check-wiki-assets.sh", smoke)
        workflow = (ROOT / ".github" / "workflows" / "build-staging.yml").read_text()
        self.assertIn("bash deploy/scripts/check-wiki-assets.sh https://armember.ir", workflow)


if __name__ == "__main__":
    unittest.main()
