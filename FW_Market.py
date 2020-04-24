#!/usr/bin/python3
# -*- coding: utf-8 -*-

import argparse
import sys
import io
import os
import struct
import time
import zlib
import hashlib
import requests
from contextlib import closing
from lxml import etree
import re
from PyQt5.QtWidgets import QPushButton,QLineEdit,QWidget,QTextEdit,QVBoxLayout,QHBoxLayout,QFileDialog,QLabel,QTableWidget,QTableWidgetItem
from PyQt5.QtCore import Qt,QThread,pyqtSignal
from PyQt5.QtGui import QIcon

CMD_SHOW_FORM  = 0x00
CMD_CLOSE_FORM = 0x01
CMD_UPDATA_OK  = 0x02

class FwThread(QThread):
    formSignal = pyqtSignal(int)
    textSignal = pyqtSignal(str)
    presSignal = pyqtSignal(int)
    def __init__(self, action, url, fileName=''):
        super(FwThread, self).__init__()

        self.action = action
        self.url = url
        self.fileName = fileName

        self.headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.77 Safari/537.36'}
        
    def run(self):
        global new_file_url
        if self.action == "get_bin_url":#获取Bin文件的下载地址
            try:
                r = requests.get(self.url, timeout=10, headers=self.headers)
                r.encoding = 'utf-8'#r.apparent_encoding
            except Exception as e:
                self.formSignal.emit(CMD_CLOSE_FORM) 

            if r.status_code == 200:
                tbodys = re.findall('<tbody>([\w\W]+?)</tbody>',r.text)
                tbody = '<tbody>' + tbodys[0] + '</tbody>'

                selector = etree.HTML(tbody)        # 转换为lxml解析的对象
                titles = selector.xpath('//td[@class="content"]/span/a/@href')    # 这里返回的是一个列表

                for each in titles:
                    title = each.strip()        # 去掉字符左右的空格
                    if title.find('.bin') > 0:
                        print(title)
                        self.textSignal.emit(title)
                        break


        elif self.action == "down_bin":#下载Bin文件

            with closing(requests.get(self.url, headers=self.headers,stream=True)) as response:
                chunkSize = 1024
                contentSize = int(response.headers['content-length'])
                dateCount = 0
                with open(self.fileName,"wb") as file:
                    for data in response.iter_content(chunk_size=chunkSize):
                        file.write(data)
                        dateCount = dateCount + len(data)
                        nowJd = (dateCount / contentSize) * 100

                        self.presSignal.emit(nowJd)

            self.formSignal.emit(CMD_UPDATA_OK)

class FW_Market(QWidget):

    def __init__(self,parent=None):
        super().__init__(parent)

        self.layout=QVBoxLayout()

        self.tbox_log=QTextEdit()

        self.setLayout(self.layout)

        self.is_First_Show = True

    def my_show(self):

        if not self.is_First_Show : return

        self.url = 'https://github.com/Ai-Thinker-Open/TB_FW_Market'
        self.headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.77 Safari/537.36'}
        r = requests.get(self.url,headers=self.headers)
        r.encoding = 'utf-8'#r.apparent_encoding
        self.html = r.text

        tbodys = re.findall('<tbody>([\w\W]+?)</tbody>',self.html)
        tbody = '<tbody>' + tbodys[0] + '</tbody>'

        selector = etree.HTML(tbody)        # 转换为lxml解析的对象
        titles = selector.xpath('//td[@class="content"]/span/a/text()')    # 这里返回的是一个列表

        self.TableWidget=QTableWidget(4,2)
        self.TableWidget.verticalHeader().setVisible(False)  # 隐藏垂直表头
        self.TableWidget.horizontalHeader().setVisible(False)  # 隐藏水平表头
        self.TableWidget.setColumnWidth(0,400)
        self.TableWidget.setColumnWidth(1,70)

        rows = self.TableWidget.rowCount()
        rows_index = 0

        for each in titles:
            title = each.strip()        # 去掉字符左右的空格
            if title.find('@') > 0:
                newItem=QTableWidgetItem(title)
                self.TableWidget.setItem(rows_index, 0, newItem)
                self.TableWidget.setCellWidget(rows_index, 1, self.buttonForRow(rows_index))

                rows_index += 1


        self.layout.addWidget(self.TableWidget)

        self.is_First_Show = False

        return 0


    def buttonForRow(self,id):
        widget=QWidget()
        # 修改
        downloadBtn = QPushButton('下载')
        downloadBtn.setStyleSheet(''' text-align : center;
        background-color : NavajoWhite;
        height : 30px;
        border-style: outset;
        font : 13px  ''')

        downloadBtn.clicked.connect(lambda:self.download(id))

        # 查看
        docBtn = QPushButton('文档')
        docBtn.setStyleSheet(''' text-align : center;
        background-color : DarkSeaGreen;
        height : 30px;
        border-style: outset;
        font : 13px; ''')

        docBtn.clicked.connect(lambda: self.document(id))

        hLayout = QHBoxLayout()
        hLayout.addWidget(downloadBtn)
        hLayout.addWidget(docBtn)
        hLayout.setContentsMargins(5,2,5,2)
        widget.setLayout(hLayout)
        return widget

    def download(self, id):
        self.mThread = FwThread(action="get_bin_url", url="https://github.com/Ai-Thinker-Open/TB_FW_Market/tree/master/" + self.TableWidget.item(id, 0).text())
        # self.mThread.formSignal.connect(self.show_form)
        self.mThread.textSignal.connect(self.save_File)
        # self.mThread.presSignal.connect(self.pressBar_refresh)
        self.mThread.start()

    def document(self, id):
        print(id)

    def save_File(self, fileUrl):
        fileName, ok = QFileDialog.getSaveFileName(self, "文件保存", "C:/", "All Files (*);;Bin Files (*.bin)")

        fileUrl.replace('blob/','')
        print("https://raw.githubusercontent.com" + fileUrl)
        if ok:
            print(fileName)

            self.mThread = FwThread(action="down_bin", url="https://raw.githubusercontent.com" + fileUrl, fileName = fileName)
            # self.mThread.formSignal.connect(self.show_form)
            #self.mThread.textSignal.connect(self.save_File)
            # self.mThread.presSignal.connect(self.pressBar_refresh)
            self.mThread.start()


if __name__ == '__main__':
    app=QApplication(sys.argv)
    win=FW_Market()
    win.show()
    sys.exit(app.exec_())