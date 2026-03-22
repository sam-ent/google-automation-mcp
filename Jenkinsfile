pipeline {
    agent none

    triggers {
        pollSCM('H/2 * * * *')
    }

    stages {
        stage('Lint') {
            agent {
                docker { image 'python:3.12-slim'; args '-u root -v pip-cache:/root/.cache/pip' }
            }
            steps {
                sh '''
                    pip install --upgrade pip -q
                    pip install -e ".[dev]" -q
                    ruff check src/ tests/
                    ruff format --check src/ tests/
                '''
            }
        }

        stage('Test') {
            agent {
                docker { image 'python:3.12-slim'; args '-u root -v pip-cache:/root/.cache/pip' }
            }
            steps {
                sh '''
                    pip install --upgrade pip -q
                    pip install -e ".[dev]" -q
                    pytest tests/ -v
                '''
            }
        }
    }

    post {
        success {
            node('') {
                withCredentials([string(credentialsId: 'github-token', variable: 'GH_TOKEN')]) {
                    sh '''
                        COMMIT=$(git rev-parse HEAD 2>/dev/null || echo "$GIT_COMMIT")
                        curl -sf -X POST \
                          -H "Authorization: token $GH_TOKEN" \
                          -H "Accept: application/vnd.github+json" \
                          -H "Content-Type: application/json" \
                          "https://api.github.com/repos/sam-ent/google-automation-mcp/statuses/$COMMIT" \
                          -d "$(printf '{"state":"success","context":"jenkins/ci","description":"Build passed","target_url":"%s"}' "$BUILD_URL")" || true
                    '''
                }
            }
        }
        failure {
            node('') {
                withCredentials([string(credentialsId: 'github-token', variable: 'GH_TOKEN')]) {
                    sh '''
                        COMMIT=$(git rev-parse HEAD 2>/dev/null || echo "$GIT_COMMIT")
                        curl -sf -X POST \
                          -H "Authorization: token $GH_TOKEN" \
                          -H "Accept: application/vnd.github+json" \
                          -H "Content-Type: application/json" \
                          "https://api.github.com/repos/sam-ent/google-automation-mcp/statuses/$COMMIT" \
                          -d "$(printf '{"state":"failure","context":"jenkins/ci","description":"Build failed","target_url":"%s"}' "$BUILD_URL")" || true
                    '''
                }
            }
        }
    }
}
