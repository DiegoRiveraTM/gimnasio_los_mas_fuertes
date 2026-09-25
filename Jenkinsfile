pipeline {
    agent any

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
            steps {
                sh '''
                    set -eu

                    for service in $SERVICES; do
                        echo "=== Probando $service ==="
                        venv="$WORKSPACE/.ci-venvs/$service"

                        python3 -m venv "$venv"
                        "$venv/bin/python" -m pip install --upgrade pip
                        "$venv/bin/python" -m pip install \
                            -r "services/$service/requirements.txt" pytest fakeredis

                        (
                            cd "services/$service"
                            "$venv/bin/python" -m pytest -q
                        )
                    done
                '''
            }
        }

        stage('Trivy filesystem scan') {
            steps {
                sh 'trivy fs --scanners vuln,misconfig,secret --severity HIGH,CRITICAL --exit-code 1 --skip-dirs "./.ci-venvs" .'
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