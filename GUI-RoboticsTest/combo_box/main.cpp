#include "mainwindow.h"
#include <QApplication>
#include <string>
int main(int argc, char *argv[])
{
    QApplication a(argc, argv);
    MainWindow w;
    w.show();
//    set<string> room = {"p", "k"};
//    for(auto itr = room.)
    return a.exec();
}
