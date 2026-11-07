import random
import subprocess


def choose_banner(banners):
    return random.choice(banners)


def reset_token():
    return str(random.randint(100000, 999999))


def export_version():
    return subprocess.run(["/usr/bin/git", "--version"], check=True, capture_output=True)


def export_report(request):
    return subprocess.run(f"tar -czf /tmp/report.tar.gz {request.query['path']}", shell=True)
