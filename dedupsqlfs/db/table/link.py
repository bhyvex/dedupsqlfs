# -*- coding: utf8 -*-

__author__ = 'sergey'

import sqlite3
from dedupsqlfs.db.table import Table

class TableLink( Table ):

    _table_name = "link"

    def create( self ):
        self.startTimer()
        c = self.getCursor()

        # Create table
        c.execute(
            "CREATE TABLE IF NOT EXISTS `%s` (" % self._table_name+
                "inode_id INTEGER UNIQUE, "+
                "target BLOB NOT NULL"+
            ");"
        )
        self.stopTimer()
        return

    def insert( self, inode, target):
        """
        :param target: bytes
        :return: int
        """
        self.startTimer()
        cur = self.getCursor()

        btarget = sqlite3.Binary(target)

        cur.execute("INSERT INTO `%s`(inode_id, target) VALUES (?, ?)" % self._table_name, (
            inode, btarget,
        ))
        item = cur.lastrowid
        self.commit()
        self.stopTimer()
        return item

    def find_by_inode( self, inode):
        """
        :param inode: int
        :return: int
        """
        self.startTimer()
        cur = self.getCursor()
        cur.execute("SELECT target FROM `%s` WHERE inode_id=?" % self._table_name, (
            inode,
        ))
        item = cur.fetchone()
        if item:
            item = item["target"]
        self.stopTimer()
        return item

    pass
