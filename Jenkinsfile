pipeline {
    agent any

    environment {
        // ---- Update these to match your environment ----
        DOCKERHUB_USER   = 'your-dockerhub-username'
        IMAGE_NAME       = 'hello-world'
        IMAGE_TAG        = "v${BUILD_NUMBER}"
        FULL_IMAGE       = "${DOCKERHUB_USER}/${IMAGE_NAME}:${IMAGE_TAG}"
        LATEST_IMAGE     = "${DOCKERHUB_USER}/${IMAGE_NAME}:latest"
        DOCKERHUB_CREDS  = credentials('docker-hub-credentials')   // Jenkins credential ID (username/password)
        KUBECONFIG_CRED  = credentials('kubeconfig-credentials')  // Jenkins "Secret file" credential ID
        GIT_REPO         = 'https://github.com/ShmuelFa/hello_world_project.git'
        GIT_BRANCH       = 'main'
    }

    options {
        timestamps()
        buildDiscarder(logRotator(numToKeepStr: '10'))
    }

    stages {

        stage('Clone Repository') {
            steps {
                echo "Cloning ${GIT_REPO} (${GIT_BRANCH})"
                git branch: "${GIT_BRANCH}", url: "${GIT_REPO}"
            }
        }

        stage('Build Application') {
            steps {
                dir('app') {
                    sh '''
                        python3 -m venv venv
                        . venv/bin/activate
                        pip install --no-cache-dir -r requirements.txt
                        pip install --no-cache-dir pytest
                        python -m pytest test_app.py -v
                    '''
                }
            }
        }

        stage('Build Docker Image') {
            steps {
                script {
                    sh "docker build -t ${FULL_IMAGE} -t ${LATEST_IMAGE} ."
                }
            }
        }

        stage('Scan Image') {
            steps {
                script {
                    // Requires Trivy installed on the Jenkins agent
                    sh "trivy image --exit-code 0 --severity HIGH,CRITICAL ${FULL_IMAGE} || true"
                }
            }
        }

        stage('Push to Docker Hub') {
            steps {
                script {
                    sh """
                        echo \$DOCKERHUB_CREDS_PSW | docker login -u \$DOCKERHUB_CREDS_USR --password-stdin
                        docker push ${FULL_IMAGE}
                        docker push ${LATEST_IMAGE}
                    """
                }
            }
        }

        stage('Deploy to Kubernetes') {
            steps {
                withEnv(["KUBECONFIG=${KUBECONFIG_CRED}"]) {
                    sh """
                        sed -i "s#IMAGE_PLACEHOLDER#${FULL_IMAGE}#g" k8s/deployment.yaml
                        kubectl apply -f k8s/deployment.yaml
                        kubectl apply -f k8s/service.yaml
                        kubectl rollout status deployment/hello-world-deployment --timeout=120s
                    """
                }
            }
        }
    }

    post {
        success {
            echo "Pipeline succeeded: ${FULL_IMAGE} deployed to Kubernetes."
        }
        failure {
            echo "Pipeline failed. Check stage logs above."
        }
        always {
            sh 'docker logout || true'
        }
    }
}
