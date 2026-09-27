pipeline {
    agent { label 'gym-ci' }

    options {
        skipDefaultCheckout(true)
        disableConcurrentBuilds()
    }

        environment {
        SERVICES = 'auth-service membership-service access-qr-service'
    }
    stages {
        stage('Checkout') {
            steps {
                deleteDir()
                checkout scm
            }
        }

        stage('Unit tests - Python microservices') {
            environment {
            DATABASE_URL = 'postgresql+psycopg://ci:ci@127.0.0.1:1/ci'
            REDIS_URL = 'redis://127.0.0.1:1/0'
            MEMBERSHIP_SERVICE_URL = 'http://127.0.0.1:1'
            SECRET_KEY = 'ci-only-signing-key-not-for-production-123456789'
            QR_SCANNER_API_KEY = 'ci-only-scanner-key'
        }
            steps {
                sh '''
                    set -eu

                    for service in $SERVICES; do
                        echo "=== Probando $service ==="
                        venv="$WORKSPACE/.ci-venvs/$service"

                        python3 -m venv "$venv"
                        "$venv/bin/python" -m pip install --upgrade pip
                        "$venv/bin/python" -m pip install \
                            -r "services/$service/requirements.txt" pytest fakeredis httpx2

                        (
                            cd "services/$service"
                            "$venv/bin/python" -m pytest -q
                        )
                    done
                '''
            }
        }

        stage('Trivy vulnerabilities and secrets') {
            steps {
                sh '''
                    trivy fs \
                    --scanners vuln,secret \
                    --severity HIGH,CRITICAL \
                    --exit-code 1 \
                    --skip-dirs .ci-venvs \
                    .
                '''
            }
        }

                stage('Trivy configuration - application') {
            steps {
                sh '''
                    set -eu

                    mkdir -p .ci-tools .ci-rendered

                    curl --fail --location --retry 3 \
                      https://dl.k8s.io/release/v1.37.0/bin/linux/amd64/kubectl \
                      -o .ci-tools/kubectl

                    curl --fail --location --retry 3 \
                      https://dl.k8s.io/release/v1.37.0/bin/linux/amd64/kubectl.sha256 \
                      -o .ci-tools/kubectl.sha256

                    echo "$(cat .ci-tools/kubectl.sha256)  .ci-tools/kubectl" | sha256sum --check -
                    chmod +x .ci-tools/kubectl

                    .ci-tools/kubectl kustomize infra/kubernetes/overlays/local \
                      > .ci-rendered/local.yaml

                    trivy config \
                      --severity HIGH,CRITICAL \
                      --exit-code 1 \
                      --skip-dirs .ci-venvs \
                      --skip-dirs .ci-tools \
                      --skip-dirs infra/terraform \
                      --skip-dirs infra/kubernetes \
                      .
                '''
            }
        }

        stage('Trivy Terraform - advisory for local demo') {
            steps {
                script {
                    // Temporal: corregir antes del despliegue en AWS.
                    def scanStatus = sh(
                        returnStatus: true,
                        script: '''
                            trivy config \
                            --severity HIGH,CRITICAL \
                            --exit-code 42 \
                            infra/terraform
                        '''
                    )

            if (scanStatus == 42) {
                unstable(
                    'Terraform has unresolved security findings. ' +
                    'AWS deployment is not approved.'
                )
            } else if (scanStatus != 0) {
                error("Terraform scan could not complete: ${scanStatus}")
            }
        }
    }
}

        stage('Semgrep SAST') {
            steps {
                sh 'semgrep scan --config p/python --error services/'
            }
        }

        stage('Build Docker images') {
            steps {
                sh '''
                    set -eu

                    for service in auth-service membership-service access-qr-service; do
                        echo "=== Construyendo imagen de $service ==="
                        docker build --pull \
                            -t "gym-lmf/$service:$BUILD_NUMBER" \
                            "services/$service"
                    done
                '''
            }
        }
    }
}