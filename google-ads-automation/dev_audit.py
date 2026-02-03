#!/usr/bin/env python3
"""
Development Audit Script
Comprehensive check of the project for development readiness
"""

import sys
import os
import subprocess
from pathlib import Path
import importlib.util


def print_section(title):
    """Print a formatted section header"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def check_python_version():
    """Check Python version"""
    print_section("Python Version")
    version = sys.version_info
    print(f"✓ Python {version.major}.{version.minor}.{version.micro}")

    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("⚠️  Warning: Python 3.8+ recommended")
        return False
    return True


def check_dependencies():
    """Check installed dependencies and their versions"""
    print_section("Installed Dependencies")

    dependencies = {
        'google-ads': 'google.ads.googleads',
        'pandas': 'pandas',
        'python-dotenv': 'dotenv',
        'pyyaml': 'yaml',
        'google-auth-oauthlib': 'google_auth_oauthlib',
    }

    all_good = True
    for package_name, import_name in dependencies.items():
        try:
            module = __import__(import_name)
            version = getattr(module, '__version__', 'unknown')
            print(f"✓ {package_name}: {version}")
        except ImportError:
            print(f"✗ {package_name}: NOT INSTALLED")
            all_good = False

    return all_good


def check_outdated_packages():
    """Check for outdated packages"""
    print_section("Outdated Packages Check")

    try:
        result = subprocess.run(
            ['pip', 'list', '--outdated', '--format=columns'],
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode == 0:
            outdated = result.stdout.strip()
            if outdated and 'Package' in outdated:
                lines = outdated.split('\n')[2:]  # Skip header
                if lines and any(line.strip() for line in lines):
                    print("⚠️  Outdated packages found:")
                    print(outdated)
                    print("\nRun: pip install --upgrade <package-name>")
                else:
                    print("✓ All packages are up to date")
            else:
                print("✓ All packages are up to date")
        else:
            print("⚠️  Could not check for outdated packages")
    except Exception as e:
        print(f"⚠️  Error checking outdated packages: {e}")


def check_project_structure():
    """Verify project directory structure"""
    print_section("Project Structure")

    project_root = Path(__file__).parent

    required_dirs = [
        'src',
        'examples',
        'config',
        'reports',
    ]

    required_files = [
        'requirements.txt',
        'README.md',
        'setup.py',
        'run.py',
        'quick_test.py',
        'src/__init__.py',
        'src/google_ads_client.py',
        'src/data_analyzer.py',
        'src/campaign_updater.py',
        'examples/simple_query.py',
        'examples/analyze_performance.py',
        'examples/update_campaigns.py',
    ]

    all_good = True

    for dir_name in required_dirs:
        dir_path = project_root / dir_name
        if dir_path.exists():
            print(f"✓ {dir_name}/")
        else:
            print(f"✗ {dir_name}/ - MISSING")
            all_good = False

    print()

    for file_name in required_files:
        file_path = project_root / file_name
        if file_path.exists():
            print(f"✓ {file_name}")
        else:
            print(f"✗ {file_name} - MISSING")
            all_good = False

    return all_good


def check_configuration_files():
    """Check for configuration files"""
    print_section("Configuration Files")

    project_root = Path(__file__).parent

    config_yaml = project_root / 'config' / 'google-ads.yaml'
    config_template = project_root / 'config' / 'google-ads.yaml.template'
    env_file = project_root / '.env'
    env_example = project_root / '.env.example'
    gitignore = project_root / '.gitignore'

    if config_yaml.exists():
        print("✓ config/google-ads.yaml (configured)")
    else:
        print("⚠️  config/google-ads.yaml - NOT FOUND (run setup.py)")

    if config_template.exists():
        print("✓ config/google-ads.yaml.template")
    else:
        print("✗ config/google-ads.yaml.template - MISSING")

    if env_file.exists():
        print("✓ .env (configured)")
    else:
        print("⚠️  .env - NOT FOUND (run setup.py)")

    if env_example.exists():
        print("✓ .env.example")
    else:
        print("✗ .env.example - MISSING")

    if gitignore.exists():
        print("✓ .gitignore")
        # Check if sensitive files are ignored
        gitignore_content = gitignore.read_text()
        if 'google-ads.yaml' in gitignore_content and '.env' in gitignore_content:
            print("  ✓ Sensitive files properly ignored")
        else:
            print("  ⚠️  Warning: Ensure .env and google-ads.yaml are in .gitignore")
    else:
        print("✗ .gitignore - MISSING")


def check_imports():
    """Test that all modules can be imported"""
    print_section("Module Import Test")

    project_root = Path(__file__).parent
    sys.path.insert(0, str(project_root))

    modules_to_test = [
        ('src.google_ads_client', 'GoogleAdsAPIClient'),
        ('src.data_analyzer', 'GoogleAdsAnalyzer'),
        ('src.campaign_updater', 'GoogleAdsUpdater'),
    ]

    all_good = True

    for module_name, class_name in modules_to_test:
        try:
            module = __import__(module_name, fromlist=[class_name])
            cls = getattr(module, class_name)
            print(f"✓ {module_name}.{class_name}")
        except ImportError as e:
            print(f"✗ {module_name}.{class_name} - IMPORT ERROR: {e}")
            all_good = False
        except AttributeError as e:
            print(f"✗ {module_name}.{class_name} - CLASS NOT FOUND: {e}")
            all_good = False

    return all_good


def check_google_ads_api_version():
    """Check Google Ads API version compatibility"""
    print_section("Google Ads API Version")

    try:
        import google.ads.googleads
        version = google.ads.googleads.__version__
        print(f"✓ google-ads library version: {version}")

        # Check API version support
        major_version = int(version.split('.')[0])
        if major_version >= 24:
            print("✓ Version is current (v24+)")
        else:
            print(f"⚠️  Version {version} may be outdated. Consider upgrading.")
            print("   Run: pip install --upgrade google-ads")

        return True
    except Exception as e:
        print(f"✗ Error checking Google Ads API version: {e}")
        return False


def check_security():
    """Check for common security issues"""
    print_section("Security Check")

    project_root = Path(__file__).parent

    # Check if credentials are accidentally committed
    config_yaml = project_root / 'config' / 'google-ads.yaml'
    env_file = project_root / '.env'

    issues_found = []

    # Check git status for sensitive files
    try:
        result = subprocess.run(
            ['git', 'status', '--porcelain'],
            capture_output=True,
            text=True,
            cwd=project_root
        )

        if result.returncode == 0:
            status_output = result.stdout

            if 'google-ads.yaml' in status_output and 'config/google-ads.yaml' in status_output:
                issues_found.append("⚠️  config/google-ads.yaml appears in git status (should be ignored)")

            if '.env' in status_output and not '.env.example' in status_output:
                issues_found.append("⚠️  .env appears in git status (should be ignored)")
    except:
        pass

    # Check file permissions
    if config_yaml.exists():
        permissions = oct(config_yaml.stat().st_mode)[-3:]
        if permissions in ['600', '640', '644']:
            print(f"✓ config/google-ads.yaml permissions: {permissions}")
        else:
            issues_found.append(f"⚠️  config/google-ads.yaml permissions: {permissions} (consider 600)")

    if env_file.exists():
        permissions = oct(env_file.stat().st_mode)[-3:]
        if permissions in ['600', '640', '644']:
            print(f"✓ .env permissions: {permissions}")
        else:
            issues_found.append(f"⚠️  .env permissions: {permissions} (consider 600)")

    if not issues_found:
        print("✓ No security issues detected")
    else:
        for issue in issues_found:
            print(issue)

    return len(issues_found) == 0


def check_documentation():
    """Check documentation completeness"""
    print_section("Documentation")

    project_root = Path(__file__).parent

    docs = {
        'README.md': 'Main documentation',
        'QUICKSTART.md': 'Quick start guide',
        'CURSOR_SETUP.md': 'Cursor IDE setup',
        'DIRECTORY_ISSUES_FIXED.md': 'Directory issue solutions',
    }

    for doc_file, description in docs.items():
        file_path = project_root / doc_file
        if file_path.exists():
            size = file_path.stat().st_size
            if size > 100:  # At least 100 bytes
                print(f"✓ {doc_file} ({description}) - {size} bytes")
            else:
                print(f"⚠️  {doc_file} exists but seems empty")
        else:
            print(f"✗ {doc_file} - MISSING")


def check_git_status():
    """Check git repository status"""
    print_section("Git Status")

    project_root = Path(__file__).parent.parent  # Go up to fuzzy-chainsaw/

    try:
        # Check if it's a git repo
        result = subprocess.run(
            ['git', 'rev-parse', '--git-dir'],
            capture_output=True,
            cwd=project_root,
            text=True
        )

        if result.returncode != 0:
            print("✗ Not a git repository")
            return False

        print("✓ Git repository detected")

        # Check current branch
        result = subprocess.run(
            ['git', 'branch', '--show-current'],
            capture_output=True,
            text=True,
            cwd=project_root
        )

        if result.returncode == 0:
            branch = result.stdout.strip()
            print(f"✓ Current branch: {branch}")

        # Check for uncommitted changes
        result = subprocess.run(
            ['git', 'status', '--porcelain'],
            capture_output=True,
            text=True,
            cwd=project_root
        )

        if result.returncode == 0:
            changes = result.stdout.strip()
            if changes:
                print("⚠️  Uncommitted changes detected:")
                print(changes[:500])  # First 500 chars
            else:
                print("✓ Working tree clean")

        return True
    except Exception as e:
        print(f"⚠️  Error checking git status: {e}")
        return False


def generate_recommendations():
    """Generate recommendations for development setup"""
    print_section("Development Recommendations")

    recommendations = []

    # Check for virtual environment
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("✓ Running in virtual environment")
    else:
        recommendations.append("Consider using a virtual environment (python3 -m venv venv)")

    # Check for IDE configuration
    project_root = Path(__file__).parent

    if (project_root / '.vscode').exists():
        print("✓ VS Code configuration found")

    if (project_root / '.idea').exists():
        print("✓ PyCharm configuration found")

    # Development tools recommendations
    dev_tools = {
        'pytest': 'Testing framework',
        'black': 'Code formatter',
        'flake8': 'Linting',
        'mypy': 'Type checking',
    }

    print("\nOptional development tools:")
    for tool, description in dev_tools.items():
        try:
            __import__(tool)
            print(f"✓ {tool} - {description} (installed)")
        except ImportError:
            print(f"  {tool} - {description} (not installed)")
            recommendations.append(f"Consider installing {tool}: pip install {tool}")

    if recommendations:
        print("\n📋 Recommendations:")
        for i, rec in enumerate(recommendations, 1):
            print(f"  {i}. {rec}")
    else:
        print("\n✓ Development setup looks good!")


def main():
    """Run comprehensive development audit"""
    print("=" * 70)
    print("  GOOGLE ADS AUTOMATION - DEVELOPMENT AUDIT")
    print("=" * 70)

    checks = [
        ("Python Version", check_python_version),
        ("Dependencies", check_dependencies),
        ("Outdated Packages", check_outdated_packages),
        ("Project Structure", check_project_structure),
        ("Configuration", check_configuration_files),
        ("Module Imports", check_imports),
        ("Google Ads API", check_google_ads_api_version),
        ("Security", check_security),
        ("Documentation", check_documentation),
        ("Git Repository", check_git_status),
    ]

    results = {}

    for name, check_func in checks:
        try:
            result = check_func()
            results[name] = result if result is not None else True
        except Exception as e:
            print(f"\n✗ Error during {name} check: {e}")
            results[name] = False

    # Generate recommendations
    generate_recommendations()

    # Summary
    print_section("SUMMARY")

    passed = sum(1 for r in results.values() if r)
    total = len(results)

    for check_name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status:10} {check_name}")

    print("\n" + "=" * 70)
    print(f"  {passed}/{total} checks passed")
    print("=" * 70)

    if passed == total:
        print("\n🎉 All checks passed! Ready for development!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} check(s) need attention")
        return 1


if __name__ == "__main__":
    sys.exit(main())
