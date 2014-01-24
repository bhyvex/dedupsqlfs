# -*- coding: utf8 -*-

__author__ = 'sergey'

from dedupsqlfs.db.mysql.table import Table

class TableInodeHashBlock( Table ):

    _table_name = "inode_hash_block"

    def create( self ):
        cur = self.getCursor()

        # Create table
        cur.execute(
            "CREATE TABLE IF NOT EXISTS `%s` (" % self.getName()+
                "`inode_id` BIGINT UNSIGNED NOT NULL, "+
                "`block_number` BIGINT UNSIGNED NOT NULL, "+
                "`hash_id` BIGINT UNSIGNED NOT NULL"+
            ")"+
            self._getCreationAppendString()
        )

        self.createIndexIfNotExists("inode_block", ('inode_id', 'block_number',), unique=True)
        self.createIndexIfNotExists("hash", ('hash_id',))
        self.createIndexIfNotExists("inode", ('inode_id',))
        return

    def insert( self, inode, block_number, hash_id):
        self.startTimer()
        cur = self.getCursor()
        cur.execute(
            "INSERT INTO `%s` " % self.getName()+
            " (`inode_id`, `block_number`, `hash_id`) VALUES (%(inode)s, %(block)s, %(hash)s)",
            {
                "inode": inode,
                "block": block_number,
                "hash": hash_id
            }
        )
        item = cur.lastrowid
        self.stopTimer('insert')
        return item

    def update( self, inode, block_number, new_hash_id):
        self.startTimer()
        cur = self.getCursor()
        cur.execute(
            "UPDATE `%s` " % self.getName()+
            " SET `hash_id`=%(hash)s WHERE `inode_id`=%(inode)s AND `block_number`=%(block)s",
            {
                "hash": new_hash_id,
                "inode": inode,
                "block": block_number
            }
        )
        item = cur.rowcount
        self.stopTimer('update')
        return item

    def delete( self, inode ):
        self.startTimer()
        cur = self.getCursor()
        cur.execute(
            "DELETE FROM `%s` " % self.getName()+
            " WHERE `inode_id`=%(inode)s",
            {
                "inode": inode
            }
        )
        count = cur.rowcount
        self.stopTimer('delete')
        return count

    def hash_by_inode_number( self, inode, block_number ):
        self.startTimer()
        cur = self.getCursor()
        cur.execute(
            "SELECT `hash_id` FROM `%s` " % self.getName()+
            " WHERE `inode_id`=%(inode)s AND `block_number`=%(block)s",
            {
                "inode": inode,
                "block": block_number
            }
        )
        item = cur.fetchone()
        if item:
            item = item["hash_id"]
        self.stopTimer('hash_by_inode_number')
        return item

    def delete_by_inode_number( self, inode, block_number ):
        self.startTimer()
        cur = self.getCursor()
        cur.execute(
            "DELETE FROM `%s` " % self.getName()+
            " WHERE `inode_id`=%(inode)s AND `block_number`=%(block)s",
            {
                "inode": inode,
                "block": block_number
            }
        )
        item = cur.rowcount
        self.stopTimer('delete_by_inode_number')
        return item

    def get_hashes_by_inode( self, inode):
        self.startTimer()
        cur = self.getCursor()
        cur.execute(
            "SELECT `hash_id` FROM `%s` " % self.getName()+
            " WHERE `inode_id`=%(inode)s",
            {
                "inode": inode
            }
        )
        items = cur.fetchall()
        self.stopTimer('get_hashes_by_inode')
        return items

    def get_by_inode( self, inode):
        self.startTimer()
        cur = self.getCursor()
        cur.execute(
            "SELECT * FROM `%s` " % self.getName()+
            " WHERE `inode_id`=%(inode)s",
            {
                "inode": inode
            }
        )
        self.stopTimer('get_by_inode')
        def fetchone():
            self.startTimer()
            item = cur.fetchone()
            self.stopTimer('get_by_inode')
            return item
        for row in iter(fetchone, None):
            yield row
        return

    def get_count_by_inode( self, inode):
        self.startTimer()
        cur = self.getCursor()
        cur.execute("SELECT COUNT(1) as `cnt` FROM `%s` " % self.getName()+
                    " WHERE inode_id=%s", (inode,))
        item = cur.fetchone()
        self.stopTimer('get_count_by_inode')
        return item['cnt']

    def get_count_hash( self, hash_id ):
        self.startTimer()
        cur = self.getCursor()
        cur.execute(
            "SELECT COUNT(1) as `cnt` FROM `%s` " % self.getName()+
            " WHERE `hash_id`=%(hash)s",
            {
                "hash": hash_id
            }
        )
        item = cur.fetchone()
        if item:
            item = item["cnt"]
        else:
            item = 0
        self.stopTimer('get_count_hash')
        return item

    def get_count_uniq_inodes(self):
        self.startTimer()
        cur = self.getCursor()
        cur.execute("SELECT COUNT(DISTINCT `inode_id`) as `cnt` FROM `%s`" % self.getName())
        item = cur.fetchone()
        if item:
            item = item["cnt"]
        else:
            item = 0
        self.stopTimer('get_count_uniq_inodes')
        return item

    def get_inode_ids(self, start_id, end_id):
        self.startTimer()
        cur = self.getCursor()
        cur.execute("SELECT DISTINCT `inode_id` FROM `%s` " % self.getName()+
                    " WHERE `inode_id`>=%s AND `inode_id`<%s", (start_id, end_id,))
        nameIds = tuple(str(item["inode_id"]) for item in cur)
        self.stopTimer('get_inode_ids')
        return nameIds

    def remove_by_inodes(self, inode_ids):
        self.startTimer()
        count = 0
        id_str = ",".join(inode_ids)
        if id_str:
            cur = self.getCursor()
            cur.execute("DELETE FROM `%s` " % self.getName()+
                        " WHERE `inode_id` IN (%s)" % (id_str,))
            count = cur.rowcount
        self.stopTimer('remove_by_inodes')
        return count

    def get_hashes_by_hashes(self, hash_ids):
        self.startTimer()

        iids = ()
        id_str = ",".join(hash_ids)
        if id_str:
            cur = self.getCursor()
            cur.execute("SELECT DISTINCT `hash_id` FROM `%s` " % self.getName()+
                            " WHERE `hash_id` IN (%s)" % (id_str,))
            iids = tuple(str(item["hash_id"]) for item in cur)

        self.stopTimer('get_hashes_by_hashes')
        return iids

    pass