import os
import tempfile
import zipfile
import shutil
import urllib.request
from cudatext import *
import cudatext_cmd

def get_url(url, fn):
    if os.path.isfile(fn):
        os.remove(fn)
    try:
        urllib.request.urlretrieve(url, fn)
    except Exception as e:
        print(e)


def do_unzip(zip_fn, to_folder):
    zip_ref = zipfile.ZipFile(zip_fn, 'r')
    zip_ref.extractall(to_folder)
    zip_ref.close()


def do_copy_dir(src, dest):
    try:
        shutil.copytree(src, dest)
    # Directories are the same
    except shutil.Error as e:
        print('Directory not copied. Error: %s' % e)
    # Any error saying that the directory doesn't exist
    except OSError as e:
        print('Directory not copied. Error: %s' % e)


def do_install_from_dir(dir_from):        
    fn_inf = os.path.join(dir_from, 'install.inf')
    if not os.path.isfile(fn_inf):
        msg_box('Cannot find install.inf in zip', MB_OK+MB_ICONERROR)
        return
        
    subdir = ini_read(fn_inf, 'info', 'subdir', '')
    typ = ini_read(fn_inf, 'info', 'type', '')
    if not subdir:
        msg_box('Cannot find subdir-value in install.inf', MB_OK+MB_ICONERROR)
        return
    if typ!='cudatext-plugin':
        msg_box('Cannot install this addon type: '+typ, MB_OK+MB_ICONERROR)
        return
        
    dir_to = os.path.join(app_path(APP_DIR_PY), subdir)
    print('Installing to: '+dir_to)
        
    dir_trash = os.path.join(app_path(APP_DIR_PY), '__trash')
    if not os.path.isdir(dir_trash):
        os.mkdir(dir_trash)
    if os.path.isdir(dir_to):
        dir_del = os.path.join(dir_trash, subdir)
        while True:
            if not os.path.isdir(dir_del):
                os.rename(dir_to, dir_del)
                break
            dir_del += '_'
        
    do_copy_dir(dir_from, dir_to)
    ed.cmd(cudatext_cmd.cmd_RescanPythonPluginsInfFiles)
    msg_box('Plugin installed to:\n'+dir_to, MB_OK+MB_ICONINFO)
    

class Command:
    def run(self):
        fn_hist = os.path.join(app_path(APP_DIR_SETTINGS), 'cuda_install_from_github.ini')
        list_hist = ['https://github.com/kvichans/cuda_find_in_files']
        if os.path.isfile(fn_hist):
            list_hist = open(fn_hist).read().splitlines()
    
        c1 = chr(1)
        id_edit = 1
        id_ok = 2
        id_cancel = 3
        res = dlg_custom('Install from Github', 456, 90, '\n'.join([]
          + [c1.join(['type=label', 'cap=&Github repo URL', 'pos=6,6,400,0'])]
          + [c1.join(['type=combo', 'items='+'\t'.join(list_hist), 'pos=6,26,450,0', 'cap='+list_hist[0]])]
          + [c1.join(['type=button', 'cap=OK', 'pos=246,60,346,0', 'props=1'])]
          + [c1.join(['type=button', 'cap=Cancel', 'pos=350,60,450,0'])]
          ))
        if not res: return
        btn, text = res
        if btn!=id_ok: return
        text = text.splitlines()
        url = text[id_edit]
        if not url: return
        
        fn = os.path.join(tempfile.gettempdir(), 'cudatext_addon.zip')
        msg_status('Downloading zip...')
        get_url(url+'/zipball/master', fn)
        msg_status('')
        if not os.path.isfile(fn):
            msg_status('Cannot download URL')
            return
        
        dir = os.path.join(tempfile.gettempdir(), 'cudatext_addon')
        if os.path.isdir(dir):
            dir_to = dir
            while True:
                dir_to += '_'
                if not os.path.isdir(dir_to):
                    os.rename(dir, dir_to)
                    break
                
        try:
            print('Unzipping: '+fn)
            do_unzip(fn, dir)
        except:
            msg_box('Cannot unzip file to temp folder', MB_OK+MB_ICONERROR)
            return
        
        #1st subdir is what to copy    
        dir_from = os.path.join(dir, os.listdir(dir)[0])
        do_install_from_dir(dir_from)

        #move new url to 1st item
        if url in list_hist:
            list_hist.remove(url)
        list_hist = [url]+list_hist
        #save history
        with open(fn_hist, 'w') as f:
            f.write('\n'.join(list_hist))
