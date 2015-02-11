# -*- coding: utf8 -*-

__author__ = 'sergey'

import os
import stat
import sys
import math
from time import time
from datetime import datetime
from dedupsqlfs.my_formats import format_size

class Subvolume(object):

    _manager = None
    _last_error = None

    def __init__(self, manager):
        """
        @param manager: FUSE wrapper
        @type  manager: dedupsqlfs.fuse.operations.DedupOperations
        """
        self._manager = manager

        self.root_mode = stat.S_IFDIR | 0o755

        pass

    def getManager(self):
        return self._manager

    def getTable(self, name):
        return self.getManager().getManager().getTable(name)

    def getLogger(self):
        return self.getManager().getLogger()

    def getLastError(self):
        return self._last_error

    def print_msg(self, msg):
        if self.getManager().getOption("verbosity") <= 0:
            return self
        sys.stdout.write(msg)
        sys.stdout.flush()
        return self

    def print_out(self, msg):
        sys.stdout.write(msg)
        sys.stdout.flush()
        return self

    def get_time_tuple(self, t):
        t_ns, t_i = math.modf(t)
        t_ns = int(t_ns * 10**9)
        return int(t_i), t_ns

    # -----------------------------------------------

    def create(self, name):
        """
        @param name: Subvolume name
        @type  name: bytes

        @return: tree node ID
        @rtype: bool|dict
        """

        if not name:
            self.getLogger().error("Define subvolume name which you need to create!")
            return False

        tableSubvol = self.getTable('subvolume')
        subvolItem = tableSubvol.find(name)
        if subvolItem:
            self.getLogger().warning("Subvolume with name %r already exists!" % name)
            return subvolItem

        subvol_id = self.getTable('subvolume').insert(name, int(time()))
        subvolItem = self.getTable('subvolume').get(subvol_id)

        tableName = self.getTable("name")
        tableTree = self.getTable('tree_' + subvolItem["hash"])
        tableInode = self.getTable('inode_' + subvolItem["hash"])

        uid, gid = os.getuid(), os.getgid()
        t_i, t_ns = self.getManager().newctime_tuple()
        nameRoot = b''

        name_id = tableName.find(nameRoot)
        if not name_id:
            name_id = tableName.insert(nameRoot)
        # Directory size: name-row-size + inode-row-size + tree-row-size
        sz = tableName.getRowSize(nameRoot) + tableInode.getRowSize() + tableTree.getRowSize()
        inode_id = tableInode.insert(2, self.root_mode, uid, gid, 0, sz, t_i, t_i, t_i, t_ns, t_ns, t_ns)
        tableTree.insert(None, name_id, inode_id)

        return subvolItem

    def list(self):
        """
        List all subvolumes
        """

        tableSubvol = self.getTable('subvolume')

        self.print_out("Subvolumes:\n")
        self.print_out("-"*(46+12+16+22+22+22+1) + "\n")
        self.print_out("%-46s| %-10s| %-14s| %-20s| %-20s| %-20s|\n" % (
            "Name", "ReadOnly", "Apparent Size", "Created", "Last mounted", "Last updated"))
        self.print_out("-"*(46+12+16+22+22+22+1) + "\n")

        for subvol_id in tableSubvol.get_ids():

            subvol = tableSubvol.get(subvol_id)

            tableInode = self.getTable("inode_" + subvol["hash"])
            apparent_size = tableInode.get_sizes()

            ctime = "---"
            if subvol["created_at"]:
                ctime = datetime.fromtimestamp(subvol["created_at"])

            mtime = "not mounted"
            if subvol["mounted_at"]:
                mtime = datetime.fromtimestamp(subvol["mounted_at"])

            utime = "not updated"
            if subvol["updated_at"]:
                utime = datetime.fromtimestamp(subvol["updated_at"])

            readonly = False
            if subvol["readonly"]:
                readonly = True

            self.print_out("%-46s| %-10r| %-14s| %-20s| %-20s| %-20s|\n" % (
                subvol["name"].decode(),
                readonly,
                format_size(apparent_size),
                ctime,
                mtime,
                utime,
                ))

        self.print_out("-"*(46+12+16+22+22+22+1) + "\n")

        return


    def prepareTreeNameIds(self):
        """
        List all subvolumes
        """

        tableSubvol = self.getTable('subvolume')
        tableTmp = self.getTable('tmp_ids')
        tableTmp.drop()
        tableTmp.create()

        for subvol_id in tableSubvol.get_ids():

            subvol = tableSubvol.get(subvol_id)

            tableTree = self.getTable("tree_" + subvol["hash"])

            curTree = tableTree.getCursor()
            curTree.execute("SELECT DISTINCT name_id FROM `%s`" % tableTree.getName())

            for node in iter(curTree.fetchone, None):
                if not tableTmp.find(node["name_id"]):
                    tableTmp.insert(node["name_id"])

        return

    def prepareIndexHashIds(self):
        """
        List all subvolumes
        """

        tableSubvol = self.getTable('subvolume')
        tableTmp = self.getTable('tmp_ids')
        tableTmp.drop()
        tableTmp.create()

        for subvol_id in tableSubvol.get_ids():

            subvol = tableSubvol.get(subvol_id)

            tableIndex = self.getTable("inode_hash_block_" + subvol["hash"])

            curIndex = tableIndex.getCursor()
            curIndex.execute("SELECT DISTINCT hash_id FROM `%s`" % tableIndex.getName())

            for node in iter(curIndex.fetchone, None):
                if not tableTmp.find(node["hash_id"]):
                    tableTmp.insert(node["hash_id"])

        return


    def remove(self, name):
        """
        @param name: Subvolume name
        @type  name: bytes
        """

        if not name:
            self.getLogger().error("Select subvolume which you need to delete!")
            return

        tableSubvol = self.getTable('subvolume')

        subvolItem = tableSubvol.find(name)
        if not subvolItem:
            self.getLogger().error("Subvolume with name %r not found!" % name)
            return False

        try:
            self.getTable('tree_' + subvolItem["hash"]).drop()
            self.getTable('inode_' + subvolItem["hash"]).drop()
            self.getTable('inode_hash_block_' + subvolItem["hash"]).drop()
            self.getTable('inode_option_' + subvolItem["hash"]).drop()
            self.getTable('link_' + subvolItem["hash"]).drop()
            self.getTable('xattr_' + subvolItem["hash"]).drop()
            self.getTable('subvolume').delete(subvolItem["id"])
        except Exception as e:
            self.getLogger().warn("Can't remove subvolume!")
            self.getLogger().error("E: %s" % e)
            import traceback
            self.getLogger().error(traceback.format_exc())
            return

        return

    def readonly(self, name, flag=True):
        """
        @param name: Subvolume name
        @type  name: bytes

        @return: success
        @rtype: bool
        """

        if not name:
            self.getLogger().error("Select subvolume which you need to delete!")
            return False

        tableSubvol = self.getTable('subvolume')

        subvol_id = tableSubvol.find(name)
        if not subvol_id:
            self.getLogger().error("Subvolume with name %r not found!" % name)
            return False

        changed = self.getTable('subvolume').readonly(subvol_id, flag)

        return changed > 0

    def get_usage(self, name, hashTypes=False):
        """
        @param name: Subvolume name
        @type  name: bytes
        """

        if not name:
            self.getLogger().error("Select subvolume which you need to process!")
            return

        tableSubvol = self.getTable('subvolume')

        subvolItem = tableSubvol.find(name)
        if not subvolItem:
            self.getLogger().error("Subvolume with name %r not found!" % name)
            return False

        tableInode = self.getTable('inode_' + subvolItem["hash"])
        tableIndex = self.getTable('inode_hash_block_' + subvolItem["hash"])

        compMethods = {}
        hashCT = {}
        hashSZ = {}

        tableHCT = self.getTable('hash_compression_type')
        tableHS = self.getTable('hash_sizes')

        hashes = tableIndex.get_hash_ids()

        dataSize = 0
        compressedSize = 0
        uniqueSize = 0
        compressedUniqueSize = 0

        for hash_id in hashes:

            if hashTypes:

                method = False
                if hash_id in hashCT:
                    method = hashCT[hash_id]
                else:
                    hctItem = tableHCT.get(hash_id)
                    if hctItem:
                        method = self.getManager().getCompressionTypeName(hctItem["type_id"])
                        hashCT[hash_id] = method

                if method:
                    compMethods[ method ] = compMethods.get(method, 0) + 1

            if hash_id in hashSZ:
                hszItem = hashSZ[hash_id]
            else:
                hszItem = tableHS.get(hash_id)
                if hszItem:
                    hashSZ[hash_id] = hszItem
                    uniqueSize += hszItem["real_size"]
                    compressedUniqueSize += hszItem["compressed_size"]

            if hszItem:
                dataSize += hszItem["real_size"]
                compressedSize += hszItem["compressed_size"]

        apparentSize = tableInode.get_sizes()
        sparseSize = apparentSize - dataSize
        dedupSize = dataSize - uniqueSize

        count_all = 0
        comp_types = {}

        if hashTypes:
            for method, cnt in compMethods.items():
                count_all += cnt
                comp_types[ cnt ] = method

        return {
            "apparentSize": apparentSize,
            "dataSize": dataSize,
            "dedupSize": dedupSize,
            "sparseSize": sparseSize,
            "uniqueSize": uniqueSize,
            "compressedSize": compressedSize,
            "compressedUniqueSize": compressedUniqueSize,
            "compressionTypes": comp_types,
            "compressionTypesAll": count_all
        }

    def report_usage(self, name):
        """
        @param name: Subvolume name
        @type  name: bytes
        """
        usage = self.get_usage(name, True)

        self.print_msg("\n")

        self.print_out("Apparent size is %s.\n" % format_size(usage["apparentSize"]) )
        self.print_out("Unique data size is %s.\n" % format_size(usage["uniqueSize"]) )
        self.print_out("Sparce data size is %s.\n" % format_size(usage["sparseSize"]) )
        self.print_out("Deduped data size is %s.\n" % format_size(usage["dedupSize"]) )

        if usage["apparentSize"]:
            self.print_out("Compressed data size is %s (%.2f %%).\n" % (
                format_size(usage["compressedSize"]), usage["compressedSize"] * 100.0 / usage["apparentSize"]
            ))
        if usage["uniqueSize"]:
            self.print_out("Compressed unique data size is %s (%.2f %%).\n" % (
                format_size(usage["compressedUniqueSize"]), usage["compressedUniqueSize"] * 100.0 / usage["uniqueSize"]
            ))

        count_all = usage["compressionTypesAll"]
        comp_types = usage["compressionTypes"]

        keys = list(comp_types.keys())
        keys.sort(reverse=True)

        if keys:
            self.print_out("Compression by types:\n")
        for key in keys:
            compression = comp_types[key]
            self.print_out(" %8s used by %.2f%% blocks\n" % (
                compression, 100.0 * key / count_all
            ))

        return

    pass