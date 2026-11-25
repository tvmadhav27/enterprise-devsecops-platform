pipeline {
    agent {
        label 'docker-agent'
    }

    options {
        timestamps()
        timeout(time: 15, unit: 'MINUTES')
    }

    stages {
        stage('Checkout Verification') {
            steps {
                echo 'Source code checked out by Jenkins.'
                sh 'pwd'
                sh 'git --version'
                sh 'ls -la'
            }
        }

        stage('Install Python Dependencies') {
            steps {
                sh '''
                    python3 -m venv "$WORKSPACE/.venv"
                    "$WORKSPACE/.venv/bin/pip" install -r application/requirements.txt
                '''
            }
        }

        stage('Python Automated Tests') {
            steps {
                dir('application') {
                    sh '''
                        PYTHONPATH="$PWD" "$WORKSPACE/.venv/bin/pytest" -v test_app.py
                    '''
                }
            }
        }

        stage('Project Validation') {
            steps {
                sh '''
                    test -f README.md
                    test -f application/app.py
                    test -f application/Dockerfile
                    echo "Project files validated successfully."
                '''
            }
        }

        stage('Docker Image Build') {
            steps {
                sh '''
                    docker build -t abc-retail-app:1.0 -t abc-retail-app:${BUILD_NUMBER} ./application
                    docker image inspect abc-retail-app:1.0
                    echo "Docker image built successfully."
                '''
            }
        }

        stage('Trivy Image Scan') {
            steps {
                sh '''
                    docker run --rm \
                      -v /var/run/docker.sock:/var/run/docker.sock \
                      -v trivy-cache:/root/.cache/trivy \
                      aquasec/trivy:0.76.2 \
                      --timeout 15m \
                      image --scanners vuln --severity HIGH,CRITICAL \
                      --format json abc-retail-app:${BUILD_NUMBER} > trivy-report.json
                '''
                archiveArtifacts artifacts: 'trivy-report.json', fingerprint: true
            }
        }

        stage('Docker Hub Push') {
            steps {
                withCredentials([
                    usernamePassword(
                        credentialsId: 'dockerhub-credentials',
                        usernameVariable: 'DOCKERHUB_USER',
                        passwordVariable: 'DOCKERHUB_TOKEN'
                    )
                ]) {
                    sh '''
                        set +x
                        echo "Publishing Docker image to Docker Hub..."

                        echo "$DOCKERHUB_TOKEN" | docker login --username "$DOCKERHUB_USER" --password-stdin

                        trap 'docker logout >/dev/null 2>&1 || true' EXIT

                        docker tag abc-retail-app:${BUILD_NUMBER} "$DOCKERHUB_USER/abc-retail-app:${BUILD_NUMBER}"

                        docker push "$DOCKERHUB_USER/abc-retail-app:${BUILD_NUMBER}"

                        echo "Docker image published successfully."
                    '''
                }
            }
        }

        stage('Kubernetes Authentication Test') {
            steps {
                withCredentials([
                    file(credentialsId: 'kubernetes-client-certificate', variable: 'K8S_CERT'),
                    file(credentialsId: 'kubernetes-client-private-key', variable: 'K8S_KEY'),
                    file(credentialsId: 'kubernetes-ca-certificate', variable: 'K8S_CA')
                ]) {
                    sh '''
                        set +x
                        echo "Checking Kubernetes certificate authentication..."

                        kubectl \
                          --server=https://host.docker.internal:54815 \
                          --tls-server-name=kubernetes \
                          --certificate-authority="$K8S_CA" \
                          --client-certificate="$K8S_CERT" \
                          --client-key="$K8S_KEY" \
                          auth can-i create deployments --namespace default

                        kubectl \
                          --server=https://host.docker.internal:54815 \
                          --tls-server-name=kubernetes \
                          --certificate-authority="$K8S_CA" \
                          --client-certificate="$K8S_CERT" \
                          --client-key="$K8S_KEY" \
                          auth can-i patch deployments.apps --namespace default
                    '''
                }
            }
        }

        stage('Kubernetes Deployment') {
            steps {
                withCredentials([
                    file(credentialsId: 'kubernetes-client-certificate', variable: 'K8S_CERT'),
                    file(credentialsId: 'kubernetes-client-private-key', variable: 'K8S_KEY'),
                    file(credentialsId: 'kubernetes-ca-certificate', variable: 'K8S_CA')
                ]) {
                    sh '''
                        set +x
                        echo "Deploying ABC Retail application using Kubernetes manifest and client certificate..."

                        TMP_MANIFEST="$(mktemp)"
                        trap 'rm -f "$TMP_MANIFEST"' EXIT

                        sed "s|image: docker.io/tvmadhav27/abc-retail-app:.*|image: docker.io/tvmadhav27/abc-retail-app:${BUILD_NUMBER}|" kubernetes/deployment.yaml > "$TMP_MANIFEST"

                        kubectl \
                          --server=https://host.docker.internal:54815 \
                          --tls-server-name=kubernetes \
                          --certificate-authority="$K8S_CA" \
                          --client-certificate="$K8S_CERT" \
                          --client-key="$K8S_KEY" \
                          apply -f "$TMP_MANIFEST"

                        echo "Waiting for Kubernetes deployment to become fully available..."

                        ATTEMPT=1
                        MAX_ATTEMPTS=60

                        while [ "$ATTEMPT" -le "$MAX_ATTEMPTS" ]; do
                            STATUS=$(kubectl \
                              --server=https://host.docker.internal:54815 \
                              --tls-server-name=kubernetes \
                              --certificate-authority="$K8S_CA" \
                              --client-certificate="$K8S_CERT" \
                              --client-key="$K8S_KEY" \
                              get deployment abc-retail-app --namespace default \
                              -o jsonpath='{.metadata.generation} {.status.observedGeneration} {.spec.replicas} {.status.updatedReplicas} {.status.availableReplicas}' 2>/dev/null) || STATUS=""

                            set -- $STATUS
                            GENERATION=${1:-0}
                            OBSERVED=${2:-0}
                            DESIRED=${3:-0}
                            UPDATED=${4:-0}
                            AVAILABLE=${5:-0}

                            echo "Attempt $ATTEMPT/$MAX_ATTEMPTS: desired=$DESIRED updated=$UPDATED available=$AVAILABLE"

                            if [ "$GENERATION" -gt 0 ] && [ "$OBSERVED" -ge "$GENERATION" ] && [ "$UPDATED" -eq "$DESIRED" ] && [ "$AVAILABLE" -eq "$DESIRED" ]; then
                                echo "Kubernetes deployment successfully rolled out."
                                break
                            fi

                            if [ "$ATTEMPT" -eq "$MAX_ATTEMPTS" ]; then
                                echo "ERROR: Kubernetes deployment did not become ready within 5 minutes."
                                exit 1
                            fi

                            ATTEMPT=$((ATTEMPT + 1))
                            sleep 5
                        done

                        kubectl \
                          --server=https://host.docker.internal:54815 \
                          --tls-server-name=kubernetes \
                          --certificate-authority="$K8S_CA" \
                          --client-certificate="$K8S_CERT" \
                          --client-key="$K8S_KEY" \
                          get pods --namespace default -l app=abc-retail-app

                        echo "Kubernetes deployment completed successfully."
                    '''
                }
            }
        }

        stage('Build Summary') {
            steps {
                echo 'Application tests, project validation and Docker image build completed.'
            }
        }
    }

    post {
        success {
            echo 'CI pipeline succeeded.'
        }
        failure {
            echo 'CI pipeline failed. Review Console Output.'
        }
    }
}
