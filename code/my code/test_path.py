# -*- coding: utf-8 -*-
import os


def listfiels(path):
    path = path.replace("\\", "/")
    mlist = os.listdir(path)

    for m in mlist:
        mpath = os.path.join(path, m)
        if os.path.isfile(mpath):
            pt = os.path.abspath(mpath)
            print pt.decode("gbk").encode("utf-8")
        else:
            pt = os.path.abspath(mpath)
            print pt
            listfiels(pt)


def walk_dir(path):
    """

    :param path:
    :return:
    """
    path = path.replace("\\", "/")
    print type(path)
    if not type(path) == unicode:
        path = unicode(path, "utf-8")
    for p, dirs, filenames in os.walk(path):
        for filename in filenames:
            print filename


# listfiels(unicode("D:/test_temp/tmp_autonav/17Q2_A5_20170630/ROOT/ALL/WIDE_BACKGROUND", "utf-8"))

walk_dir(unicode(r'C:\Users\shchshan\Desktop\b', "utf-8"))
walk_dir(r'C:\Users\shchshan\Desktop\b')
