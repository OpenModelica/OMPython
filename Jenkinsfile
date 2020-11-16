pipeline {
  agent none
  stages {
    stage('test') {
      parallel {
        stage('python2') {
          agent {
            label 'linux'
          }
          steps {
            script {
              def deps = docker.build('ompython-jenkins-python2', '--pull .jenkins/python2')
              def dockergid = sh (script: 'stat -c %g /var/run/docker.sock', returnStdout: true).trim()
              sh "docker pull openmodelica/openmodelica:v1.16.0-minimal" // Avoid timeout
              deps.inside("-v /var/run/docker.sock:/var/run/docker.sock --network=host --pid=host --group-add '${dockergid}'") {
                sh 'python2 setup.py build'
                timeout(3) {
                  sh 'python2 /usr/local/bin/py.test -v --junitxml py3.xml tests'
                }
                sh 'HOME="$PWD" python2 setup.py install --user'
                junit 'py2.xml'
              }
            }
          }
        }
        stage('python3') {
          agent {
            label 'linux'
          }
          steps {
            script {
              def deps = docker.build('ompython-jenkins-python3', '--pull .jenkins/python3')
              def dockergid = sh (script: 'stat -c %g /var/run/docker.sock', returnStdout: true).trim()
              sh "docker pull openmodelica/openmodelica:v1.16.0-minimal" // Avoid timeout
              deps.inside("-v /var/run/docker.sock:/var/run/docker.sock --network=host --pid=host --group-add '${dockergid}'") {
                sh 'python3 setup.py build'
                timeout(3) {
                  sh 'python3 /usr/local/bin/py.test -v --junitxml py3.xml tests'
                }
                sh 'HOME="$PWD" python3 setup.py install --user'
                junit 'py3.xml'
              }
            }
          }
        }
      }
    }
  }
}
