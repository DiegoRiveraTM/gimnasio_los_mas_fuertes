pipeline {
    agent any

    options {
        skipDefaultCheckout(true)
        disableConcurrentBuilds()
    }

    environment {
        SERVICES = 'services/auth-service services/membership-service services/access-qr-service'
    }

    stages {
        stage('Checkout') {
            steps {
                deleteDir()
                checkout scm
            }
        }

        stage('Python tests') {
            steps {
                sh '''
                    set -eu

                    for service in $SERVICES; do
                        echo "Probando $service"

                        docker run --rm \
                          -v "$WORKSPACE/$service:/app" \
                          -w /app \
                          python:3.12-slim \
                          sh -c 'pip install --disable-pip-version-check -r requirements.txt pytest && pytest -q'
                    done
                '''
            }
        }

        stage('Trivy filesystem scan') {
            steps {
                sh 'trivy fs --scanners vuln,misconfig,secret --severity HIGH,CRITICAL --exit-code 1 .'
            }
        }

        stage('Semgrep SAST') {
            steps {
                sh 'semgrep scan --config p/python --error services/'
            }
        }

        stage('Build and scan Docker images') {
            steps {
                sh '''
                    set -eu

                    for service in $SERVICES; do
                        name=$(basename "$service")
                        image="gym-mvp/$name:${BUILD_NUMBER}"

                        echo "Construyendo $image"
                        docker build --pull -t "$image" "$service"

                        echo "Escaneando $image"
                        trivy image --exit-code 1 --severity HIGH,CRITICAL "$image"
                    done
                '''
            }
        }
    }
}