from setuptools import setup

package_name = "winros_robot_adapters"

setup(
    name=package_name,
    version="0.1.0",
    packages=[package_name],
    data_files=[
        ("share/ament_index/resource_index/packages", [f"resource/{package_name}"]),
        (f"share/{package_name}", ["package.xml"]),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="WinROS contributors",
    maintainer_email="maintainers@example.com",
    description="Dry-run hardware adapter skeletons for WinROS.",
    license="MIT",
    entry_points={
        "console_scripts": [
            "dry_run_adapter = winros_robot_adapters.adapter_node:main",
        ],
    },
)

