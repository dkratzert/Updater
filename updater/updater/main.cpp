#include <QtCore>
#include <QtNetwork/QNetworkAccessManager>
#include <QtNetwork/QNetworkReply>
#include <QProcess>

const QString program_name = "YourProgramName";
const QString program_url = "https://dkratzert.de/files/your_program_folder/YourProgramName-setup-x64-v%1.exe";
const QString sha_url = "https://dkratzert.de/files/your_program_folder/YourProgramName-setup-x64-v%1-sha512.sha";

QStringList getCommandLineArguments(int argc, char* argv[]) {
    QStringList args;
    for (int i = 1; i < argc; ++i) {
        args << QString::fromUtf8(argv[i]);
    }
    return args;
}

void showHelp() {
    qDebug() << "############ Program updater V7 #################";
    qDebug() << "Command line options:";
    qDebug() << "-v version  : Version number of the installer executable";
    qDebug() << "-p name     : Program name";
}

void killProgramInstances() {
    if (QSysInfo::productType() == "windows") {
        QProcess::execute("taskkill /f /im " + program_name + ".exe", QStringList());
        //QProcess::execute("cls", []);
        QThread::msleep(1000);
    }
}

bool isProgramRunning() {
    if (QSysInfo::productType() == "windows") {
        QProcess process;
        process.start("tasklist", QStringList());
        process.waitForFinished();
        QString output = process.readAllStandardOutput().toLower();
        return output.contains(program_name.toLower());
    }
    return false;
}

QString downloadFile(const QString& url, const QString& destination) {
    QNetworkAccessManager manager;
    QEventLoop loop;
    QNetworkReply* reply = manager.get(QNetworkRequest(QUrl(url)));
    QObject::connect(reply, &QNetworkReply::finished, &loop, &QEventLoop::quit);
    loop.exec();

    if (reply->error() != QNetworkReply::NoError) {
        qDebug() << "Failed to download file from:" << url;
        return "";
    }

    QFile file(destination);
    if (file.open(QIODevice::WriteOnly)) {
        file.write(reply->readAll());
        file.close();
        return destination;
    }
    return "";
}

bool verifyChecksum(const QString& file_path, const QString& sha_url) {
    QFile file(file_path);
    if (!file.open(QIODevice::ReadOnly)) {
        qDebug() << "Failed to open file for checksum verification:" << file_path;
        return false;
    }
    QByteArray file_data = file.readAll();
    file.close();

    QString expected_sha = downloadFile(sha_url, "checksum.sha");
    if (expected_sha.isEmpty()) {
        qDebug() << "Failed to download checksum file:" << sha_url;
        return false;
    }

    QFile checksum_file("checksum.sha");
    if (!checksum_file.open(QIODevice::ReadOnly)) {
        qDebug() << "Failed to open checksum file for verification";
        return false;
    }
    QByteArray checksum_data = checksum_file.readAll();
    checksum_file.close();

    return QCryptographicHash::hash(file_data, QCryptographicHash::Sha512).toHex() == checksum_data;
}

bool runUpdater(const QString& filename) {
    if (QSysInfo::productType() == "windows") {
        QProcess::startDetached(filename, QStringList());
        return true;
    }
    return false;
}

int main(int argc, char* argv[]) {
    QCoreApplication app(argc, argv);
    QStringList args = getCommandLineArguments(argc, argv);

    if (args.size() < 2) {
        showHelp();
        return 4;
    }

    QString version, program;
    for (int i = 0; i < args.size(); ++i) {
        if (args[i] == "-v" && i + 1 < args.size()) {
            version = args[i + 1];
        } else if (args[i] == "-p" && i + 1 < args.size()) {
            program = args[i + 1];
        }
    }

    if (version.isEmpty() || program.isEmpty()) {
        qDebug() << "Invalid command line options.";
        showHelp();
        return 4;
    }

    QString program_url_formatted = program_url.arg(version);
    QString program_path = QString("%1-setup.exe").arg(program);

    killProgramInstances();

    if (isProgramRunning()) {
        killProgramInstances();
        if (isProgramRunning()) {
            return 3;
        }
    }

    QString tmp_dir = QCoreApplication::applicationDirPath();
    QString downloaded_update = downloadFile(program_url_formatted, program_path);

    if (!downloaded_update.isEmpty()) {
        if (verifyChecksum(downloaded_update, sha_url.arg(version))) {
            if (runUpdater(downloaded_update)) {
                qDebug() << "Finished successfully.";
            } else {
                qDebug() << "Failed to run updater.";
            }
        } else {
            qDebug() << "Checksum Failed. Update with this file not possible.";
        }
    } else {
        qDebug() << "No update found. Giving up.";
        if (QSysInfo::productType() == "windows") {
            //QProcess::execute("pause");
        }
    }

    return 0;
}
