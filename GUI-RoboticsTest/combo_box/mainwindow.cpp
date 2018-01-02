#include "mainwindow.h"
#include "ui_mainwindow.h"
#include <QPixmap>

MainWindow::MainWindow(QWidget *parent) :
    QMainWindow(parent),
    ui(new Ui::MainWindow)
{
    ui->setupUi(this);
    QPixmap pix(":/resource/resource/TurtleBot.jpg");
    int w = ui->imageLabel->width();
    int h = ui->imageLabel->height();
    ui->imageLabel->setPixmap(pix.scaled(w,h,Qt::KeepAspectRatio));
    for (auto itr = room_ID.begin(); itr!=room_ID.end(); ++itr){
        QString room_name = QString::fromStdString(*itr);
        ui->startComboBox->addItem(room_name);
        ui->endComboBox->addItem(room_name);
    }
}
//

MainWindow::~MainWindow()
{
    delete ui;
}
