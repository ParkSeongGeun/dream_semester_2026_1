// ============================================
// 맘편한 이동 백엔드 - Jenkins Declarative Pipeline (14주차)
//   Checkout → Lint → Test → Docker Build → Push to ECR
//   13주차 GitHub Actions(ci.yml)와 동일한 단계를 Jenkins 로 재구성
//
//   설계 노트: 테스트/운영 빌드는 공식 python:3.12-slim 기반 Docker 이미지로 수행한다.
//   Jenkins 노드(ARM64)에서 직접 pip install 하면 asyncpg/pydantic-core 가
//   네이티브 컴파일에 실패하므로, wheel 이 정상 제공되는 컨테이너 안에서 빌드한다.
// ============================================
pipeline {
    agent any

    environment {
        ECR_REPOSITORY = 'comfortablemove-backend'
        AWS_REGION     = 'ap-northeast-2'
        // per-Dockerfile ignore(Dockerfile.test.dockerignore) 적용을 위해 BuildKit 활성화
        DOCKER_BUILDKIT = '1'
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

        // flake8 은 순수 파이썬이라 Jenkins 노드 venv 에서 바로 실행 가능 (컴파일 불필요)
        stage('Lint') {
            steps {
                dir('backend') {
                    sh '''
                        python3 -m venv .venv
                        . .venv/bin/activate
                        pip install -q --upgrade pip
                        pip install -q flake8
                        flake8 app/ --count --statistics
                    '''
                }
            }
        }

        // Dockerfile.test(python:3.12-slim) 로 테스트 이미지를 빌드한 뒤 컨테이너에서 pytest 실행
        stage('Test') {
            steps {
                sh '''
                    docker build -f backend/Dockerfile.test -t comfortablemove-test:${IMAGE_TAG} ./backend
                    mkdir -p backend/test-results
                    docker run --name cm-test-${BUILD_NUMBER} \
                        -e ENVIRONMENT=development \
                        -e SEOUL_BUS_API_KEY=test_key_for_ci \
                        -e SECRET_KEY=ci-test-secret-key \
                        -e DATABASE_URL=postgresql+asyncpg://test:test@localhost:5432/test \
                        -e REDIS_URL=redis://localhost:6379/0 \
                        comfortablemove-test:${IMAGE_TAG} \
                        python -m pytest tests/ -v -m "not slow" \
                            --cov=app --cov-report=term-missing \
                            --junitxml=test-results/junit.xml
                '''
            }
            post {
                always {
                    // 컨테이너 안에서 생성된 junit 리포트를 workspace 로 추출 후 게시
                    sh '''
                        docker cp cm-test-${BUILD_NUMBER}:/app/test-results/junit.xml \
                            backend/test-results/junit.xml || true
                        docker rm -f cm-test-${BUILD_NUMBER} || true
                    '''
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
            // 빌드 산출물(테스트 이미지) 정리 + Slack 알림(SLACK_CHANNEL 설정 시에만)
            sh 'docker rmi comfortablemove-test:${IMAGE_TAG} || true'
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
