pipeline {
    agent any

    triggers{
        githubPush()
    }

    stages {
        stage('checkout') {
            steps {
                checkout scm
            }
        }

        stage('install dependencies') {
            steps {
                sh '''
                python3 -m venv venv
                . venv/bin/activate
                pip install --upgrade pip
                pip install -r requirements.txt
                '''
            }
        }

        stage('Tests') {
            steps {
                sh '''
                . venv/bin/activate
                python -m pytest
                '''
            }
        }

        stage('build docker image') {
            steps {
                sh 'docker build -t kellidan/flask-app:latest .'
            }
        }

        stage('push to docker hub') {
            steps {
                withCredentials([usernamePassword(
                    credentialsId: 'docker-creds', 
                    usernameVariable: 'DOCKER_USER',
                    passwordVariable: 'DOCKER_PASS'
                )]) {
                    sh ''' 
                        echo "$DOCKER_PASS" | docker login -u "$DOCKER_USER" --password-stdin
                        docker push kellidan/flask-app:latest
                    '''
                }
            }
        }
    }
    post{
        success{
            emailtext{
                subject:"Success $(env.JOB_NAME) [#${env.BUILD_NUMBER}]"
                body: """
                    <h2> Jenkins build successful</h2>
                    <p>
                        <b>URL</B>: $(env.BUILD_URL)
                    </p>
                    """,
                to: "kellidanfernandes57@gmail.com"
                }
            }
        failure{
            emailtext{
                subject:"Failure $(env.JOB_NAME) [#${env.BUILD_NUMBER}]"
                body: """
                    <h2> Jenkins build failed</h2>
                    <p>
                        <b>URL</B>: $(env.BUILD_URL)
                    </p>
                    """,
                to: "kellidanfernandes57@gmail.com"
                }
            }
        }
    }
}