# kpi-dash

A source code repository for uploaded applications with automated Docker image building and publishing to JFrog Artifactory.

| latest version | type | description |
| --- | --- | --- |
| [![kpi-functional-dashboard-backend](https://gitlab-master.nvidia.com/ape-repo/astra-projects/kpi-dash/-/jobs/artifacts/main/raw/public/badges/app-kpi-functional-dashboard-backend.svg?job=multi_release:finalize)](https://gitlab-master.nvidia.com/ape-repo/astra-projects/kpi-dash/-/jobs/artifacts/main/raw/public/badges/app-kpi-functional-dashboard-backend.svg?job=multi_release:finalize) | [![PyPI](https://img-shield-cloudsre.gcp-int.nvidia.com/badge/PyPI-3775A9?logo=pypi&logoColor=fff)](#) | NAT React Agent Blueprint for Astra |

🛑 This table is automatically generated. Please do not modify it!!!

## 📁 Repository Structure

**`apps/`** - Source code for containerized applications. Each subdirectory represents a separate microservice with its own Dockerfile and dependencies. **Your uploaded application source code is here**.

## 🚀 Getting Started

This repository is configured to automatically build and push Docker images to JFrog Artifactory when you push code to the repository.


### Updating Your Applications

1. **Modify your code**: Update the source code in the respective `apps/` directories
2. **Update Dockerfiles**: Modify the Dockerfiles in each app directory to match your application requirements
3. **Update dependencies**: Modify requirements.txt, package.json, or other dependency files as needed
4. **Push changes**: Commit and push your changes to trigger the CI/CD pipeline

### CI/CD Pipeline

The GitLab CI pipeline will automatically:
- Build Docker images for each application in the `apps/` directory
- Tag images with version numbers
- Push images to JFrog Artifactory (`artifactory.nvidia.com/continum`)
- Generate release badges and version tracking

### Image Naming Convention

Images will be published to JFrog with the following naming pattern:
- `artifactory.nvidia.com/continum/kpi-functional-dashboard:{version}`

Where `{version}` follows semantic versioning (e.g., 1.0.0, 1.0.1, etc.)

## 🔧 Configuration

- **Dockerfile**: Each app directory contains a Dockerfile that you can customize for your application's specific needs
- **requirements.txt / package.json**: Update dependencies as needed for your technology stack
- **version.py**: Version numbers are automatically managed by the CI/CD pipeline
- **.gitlab-ci.yml**: CI/CD configuration is managed at the repository level

## 📊 Monitoring & Access

### Pipeline Status
Monitor your builds and deployments through:
- GitLab CI/CD pipelines in this repository
- Release badges (shown in the table above)

### Accessing Built Images
Once built, your Docker images will be available at:
```
artifactory.nvidia.com/it-continum/kpi-functional-dashboard:{specific-version}
```

## 🔧 Troubleshooting

### Common Issues
- **Build failures**: Check your Dockerfile syntax and ensure all dependencies are properly specified
- **Missing dependencies**: Update requirements.txt or package.json with all required packages
- **Docker context issues**: Ensure your Dockerfile is in the correct app subdirectory

### Getting Help
- Check GitLab CI/CD pipeline logs for detailed error messages
- Verify your application works locally with `docker build` before pushing
- Contact the platform team for infrastructure-related issues


### Maintainers
Galia Plotinsky - galiaf@nvidia.com
