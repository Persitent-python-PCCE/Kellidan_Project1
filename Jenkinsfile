pipeline {
    agent any

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
                sh 'docker build -t kellidan/flask-app:latest'
            }
        }

        stage('push to docker hub') {
            steps {
                withCredentials([usernamePassword(
                    credentialsId: 'docker-creds', 
                    usernameVariable: 'DOCKER-USER',
                    passwordVariable: 'DOCKER-PASS')]) 
                    {
                        sh ''' 
                        echo $DOCKER-PASS | docker login -u $DOCKER-USER --password-stdin 
                        docker push kellidan/flask-app:latest
                        '''
                }
            }
        }
    }
}