// ============================================
// 맘편한 이동 백엔드 - Jenkins Declarative Pipeline (14주차)
//   Checkout → Build → Lint → Test → Docker Build → Push to ECR
//   13주차 GitHub Actions(ci.yml)와 동일한 단계를 Jenkins 로 재구성
// ============================================
pipeline {
    agent any

    environment {
        ECR_REPOSITORY = 'comfortablemove-backend'
        AWS_REGION     = 'ap-northeast-2'
        // pytest 용 환경변수 (conftest 의 SQLite DI override 가 실제 쿼리를 처리)
        DATABASE_URL      = 'postgresql+asyncpg://test:test@localhost:5432/test'
        REDIS_URL         = 'redis://localhost:6379/0'
        ENVIRONMENT       = 'development'
        SEOUL_BUS_API_KEY = 'test_key_for_ci'
        SECRET_KEY        = 'ci-test-secret-key'
    }

    options {
        timeout(time: 30, unit: 'MINUTES')
        disableConcurrentBuilds()
        buildDiscarder(logRotator(numToKeepStr: '10'))
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
                script {
                    env.IMAGE_TAG = (env.GIT_COMMIT ?: env.BUILD_NUMBER).take(7)
                }
                sh 'git log -1 --oneline'
            }
        }

        stage('Build') {
            steps {
                dir('backend') {
                    sh '''
                        python3 -m venv .venv
                        . .venv/bin/activate
                        python -m pip install --upgrade pip
                        pip install -r requirements.txt flake8
                    '''
                }
            }
        }

        stage('Lint') {
            steps {
                dir('backend') {
                    sh '''
                        . .venv/bin/activate
                        flake8 app/ --count --statistics
                    '''
                }
            }
        }

        stage('Test') {
            steps {
                dir('backend') {
                    sh '''
                        . .venv/bin/activate
                        pytest tests/ -v -m "not slow" \
                            --cov=app --cov-report=xml:coverage.xml \
                            --junitxml=test-results/junit.xml
                    '''
                }
            }
            post {
                always {
                    junit allowEmptyResults: true, testResults: 'backend/test-results/junit.xml'
                }
            }
        }

        stage('Docker Build') {
            steps {
                sh 'docker build -t ${ECR_REPOSITORY}:${IMAGE_TAG} ./backend'
                sh 'docker images ${ECR_REPOSITORY}:${IMAGE_TAG}'
            }
        }

        // ECR_REGISTRY 가 주입된 경우에만 실행 (미설정 시 graceful skip)
        stage('Push to ECR') {
            when {
                expression { return env.ECR_REGISTRY?.trim() }
            }
            steps {
                sh '''
                    aws ecr get-login-password --region ${AWS_REGION} \
                      | docker login --username AWS --password-stdin ${ECR_REGISTRY}
                    docker tag ${ECR_REPOSITORY}:${IMAGE_TAG} ${ECR_REGISTRY}/${ECR_REPOSITORY}:${IMAGE_TAG}
                    docker tag ${ECR_REPOSITORY}:${IMAGE_TAG} ${ECR_REGISTRY}/${ECR_REPOSITORY}:latest
                    docker push ${ECR_REGISTRY}/${ECR_REPOSITORY}:${IMAGE_TAG}
                    docker push ${ECR_REGISTRY}/${ECR_REPOSITORY}:latest
                '''
            }
        }
    }

    post {
        success {
            echo "✅ Pipeline 성공: ${env.ECR_REPOSITORY}:${env.IMAGE_TAG}"
        }
        failure {
            echo "❌ Pipeline 실패 — 콘솔 로그 확인 필요"
        }
        always {
            // Slack 알림 (SLACK_CHANNEL 설정 시에만 발송)
            script {
                if (env.SLACK_CHANNEL?.trim()) {
                    slackSend(
                        channel: env.SLACK_CHANNEL,
                        color: currentBuild.currentResult == 'SUCCESS' ? 'good' : 'danger',
                        message: "맘편한 이동 빌드 #${env.BUILD_NUMBER} — ${currentBuild.currentResult} (${env.JOB_NAME})"
                    )
                }
            }
        }
    }
}
