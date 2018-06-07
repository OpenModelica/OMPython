pipeline {
  agent {
    docker {
      // Large image with full OpenModelica build dependencies; lacks omc and OMPython
      image 'openmodelica/build-deps'
    }
  }
  options {
    disableConcurrentBuilds()
  }
  stages {
    stage('setup') {
      steps {
        sh '''
# Install the omc package; should only take a few seconds
apt-get update
apt-get install -qy gnupg wget ca-certificates apt-transport-https sudo
echo "deb https://build.openmodelica.org/apt `lsb_release -sc`  release" > /etc/apt/sources.list.d/openmodelica.list
wget https://build.openmodelica.org/apt/openmodelica.asc -O- | apt-key add -
apt-get update
apt-get install -qy --no-install-recommends omc
'''
      }
    }
    stage('build') {
      parallel {
        stage('python2') {
          steps {
            // OpenModelica does not like running as root
            sh 'chown -R nobody .'
            sh 'pip2 install pytest'
            sh 'sudo -u nobody python2 setup.py build'
            timeout(3) {
              sh 'sudo -u nobody py.test -v --junitxml py2.xml tests/*.py'
            }
            sh 'python2 setup.py install'
            junit 'py2.xml'
          }
        }
        stage('python3') {
          steps {
            // OpenModelica does not like running as root
            sh 'chown -R nobody .'
            sh 'pip3 install pytest'
            sh 'sudo -u nobody python3 setup.py build'
            timeout(3) {
              sh 'sudo -u nobody py.test -v --junitxml py3.xml tests/*.py'
            }
            sh 'python3 setup.py install'
            junit 'py3.xml'
          }
        }
      }
    }
  }
}
