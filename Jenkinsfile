pipeline {
    agent {
        label 'docker-agent'
    }

    options {
        timestamps()
        timeout(time: 10, unit: 'MINUTES')
    }

    stages {
        stage('Checkout Verification') {
            steps {
                echo 'Source code is checked out by Jenkins.'
                sh 'pwd'
                sh 'git --version'
                sh 'ls -la'
            }
        }

        stage('Project Validation') {
            steps {
                sh '''
                    test -f README.md
                    test -f application/README.md
                    echo "Project files validated successfully."
                '''
            }
        }

        stage('Build Summary') {
            steps {
                echo 'Initial CI pipeline completed.'
                echo 'Next: add application build, security scanning, and deployment.'
            }
        }
    }

    post {
        success {
            echo 'CI pipeline succeeded.'
        }
        failure {
            echo 'CI pipeline failed. Review the console output.'
        }
    }
}
