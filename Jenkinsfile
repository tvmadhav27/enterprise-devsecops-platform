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
                    docker build -t abc-retail-app:1.0 ./application
                    docker image inspect abc-retail-app:1.0
                    echo "Docker image built successfully."
                '''
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
