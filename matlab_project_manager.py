import os
import sys
import argparse
import shutil
import git
from git import Repo
import subprocess
import warnings
from collections import defaultdict
import re

def split_repo_name(repo_url):
    parts = os.path.split(repo_url.strip())
    filtered_parts = (parts[0],os.path.splitext(parts[1])[0])
    return filtered_parts

def remove_https_dep_dups(repo_url_set):
    md = defaultdict(list)
    for repo_url in repo_url_set:
        cleaned_repo_url = repo_url.strip()
        extless_repo = os.path.splitext(cleaned_repo_url)[0]
        if "@" in extless_repo:
            tmp = re.split('@',extless_repo)[-1]
            repo_name = tmp.split(":")[-1].strip()
        elif "http" in extless_repo:
            tmp = re.split('://',extless_repo)[-1]
            repo_name = tmp.split('/', 1)[-1].strip()
        
        md[repo_name].append(cleaned_repo_url)

    deduped = []
    for key in md.keys():
        l = md[key]
        deduped_l = [dep for dep in l if "http" not in dep]
        deduped+=deduped_l

    return deduped

def check_for_repo_name_clashes(repo_url_set):
    md = defaultdict(list)
    for repo_url in repo_url_set:
        repo_parts = split_repo_name(repo_url)
        md[repo_parts[1]].append(repo_url.strip())
    
    for key in md.keys():
        if len(md[key])>1:
            dup_list = "\n".join(md[key])+"\n"
            msg = '\n'+'#'*50 + "\n\nMultiple repos named \'%s\' will be added to deps: \n\n %s \n There is a possibility for name clashes.\n\n"%(key,dup_list) +'#'*50+'\n'
            raise Exception(msg)
            
        
    

def mkdirp(path):
    if not os.path.isdir(path):
        os.makedirs(path)
        return True
    return False
    

def find_dirs(path):
    allpaths = []
    for (folder, folders, files) in os.walk(path):
        for f in folders:
            child = os.path.join(folder, f)
            allpaths.append(child)        
    return allpaths

def touch(path):
    open(path, 'a').close()
    
def write_gitignore(gitignore_file):
    # add all repos inside deps/ folder to .gitignore file, and deduplicate
    touch(gitignore_file)
    gif=open(gitignore_file,'r')
    gif_lines = gif.readlines()
    gif.close()
    gif_lines = set(gif_lines)
    gif_lines.add('deps/')
    gif_lines = list(gif_lines)
    os.remove(gitignore_file)
    gif=open(gitignore_file,'w')
    gif.writelines(['%s\n' % tmp_str.strip() for tmp_str in gif_lines])
    gif.close()
    
def write_addpath(deps_folder, new_deps_folder, project_src_folder, addpath_script):
    # find all source containing folders recursively (in /deps/, /new_deps/ and /src/), and add to a matlab project_addpath.m script        
    deps_dirs = find_dirs(deps_folder)
    new_deps_dirs = find_dirs(new_deps_folder)
    project_src_dirs = find_dirs(project_src_folder)
    addpath_candidate_folders = deps_dirs+new_deps_dirs+project_src_dirs
    
    folder_filter = lambda tmpf : not (('.git' in tmpf) or ('deprecated' in tmpf) or ('@' in tmpf))        
    addpath_folders = [ tmpf2 for tmpf2 in addpath_candidate_folders if folder_filter(tmpf2) ]
    addpath_file_lines = [ 'addpath %s \n' % tmpf3.strip() for tmpf3 in addpath_folders ]
    os.remove(addpath_script)
    addpath_script_handle=open(addpath_script,'w')
    addpath_script_handle.writelines(addpath_file_lines)
    addpath_script_handle.close()    
    
    
def read_top_level_requirements(matlab_requirements_file):
    requirements_handle = open(matlab_requirements_file,'r')
    requirements =requirements_handle.readlines()
    requirements_handle.close()
    cleaned_requirements = [ line for line in requirements if (not '#' in line) and (not line.strip()=="") ] 
    return cleaned_requirements

def clone_new_deps(cleaned_requirements, deps_folder):
    # in the folder ./deps clone each repo specified in the matlab_requirements.txt file, if it doesn't already exist
    new_deps = []
    for repo in cleaned_requirements:
        dep_folder = (repo.strip().split('/')[-1]).split('.')[0]
        print "Checking for: "+ dep_folder
        if not os.path.isdir(os.path.join(deps_folder,dep_folder)):
            print "--------  Fetching %s --------" % repo.strip()
            dep_folder = os.path.join(deps_folder,dep_folder)
            new_deps.append(dep_folder)
            Repo.clone_from(repo.strip(), dep_folder)
    return new_deps

def pull_dep_changes(deps_folder, just_cloned):
    # for each repo cloned into deps, fetch changes. ANY UPDATES MUST BE MERGED MANUALLY.    
    deps_child_folders = os.listdir(deps_folder)
    for deps_child_folder in deps_child_folders:
        if(os.path.isdir(os.path.join(deps_folder,deps_child_folder))):
            dep_folder = os.path.join(deps_folder,deps_child_folder)
            if not dep_folder in just_cloned:
                g = git.cmd.Git(dep_folder)
                print "Pulling changes for %s" % deps_child_folder
                g.pull()

def find_child_dependencies(project_folder):
    # find all matlab_requirements.txt files in /deps/ folder (i.e. in child repos), and add them to the matlab_requirements.txt of the top-level project. THEN RUN THIS COMMAND AGAIN.
    all_matlab_requirements_files = subprocess.check_output("find %s -type f -mindepth 2 -name matlab_requirements.txt " % project_folder, shell=True).split('\n')
    child_matlab_requirements=[]
    for mrf in all_matlab_requirements_files:
        if not mrf=='':
            mrf_contents = open(mrf,'r').readlines()
            child_matlab_requirements = child_matlab_requirements+mrf_contents

    all_matlab_requirements_sorted = set(child_matlab_requirements)
    return all_matlab_requirements_sorted

def write_new_requirements_file(matlab_requirements_file, new_requirements):
    os.remove(matlab_requirements_file)
    requirements_handle = open(matlab_requirements_file,'w')
    requirements_handle.writelines(['%s\n' % new_req.strip() for new_req in new_requirements])
    requirements_handle.close()

if __name__=="__main__":
    parser = argparse.ArgumentParser(description='Matlab project manager. Requires gitpython (installable via pip)')
    parser.add_argument('-p','--project_folder', help='folder containing matlab project', required=True)
    args = parser.parse_args()
    arg_dict = vars(args)    
    project_folder = arg_dict['project_folder']

    project_src_folder=os.path.join(project_folder,'src')
    deps_folder=os.path.join(project_folder,'deps')
    new_deps_folder=os.path.join(project_folder,'new_deps')
    cache_folder=os.path.join(project_folder,'cache')
    data_folder=os.path.join(project_folder,'data')
    output_folder=os.path.join(project_folder,'output')
    matlab_requirements_file=os.path.join(project_folder,'matlab_requirements.txt')
    addpath_script=os.path.join(project_folder,'project_addpath.m')
    gitignore_file=os.path.join(project_folder,'.gitignore')

    if os.path.isfile(matlab_requirements_file):
        
        # make all required project sub-folders
        mkdirp(new_deps_folder); mkdirp(cache_folder); mkdirp(data_folder)
        mkdirp(output_folder); mkdirp(deps_folder)
        

        top_level_requirements = read_top_level_requirements(matlab_requirements_file)
        all_deps = set(top_level_requirements)
        just_cloned = []
        while(True):
            cleaned_https_deps = remove_https_dep_dups(all_deps)
            check_for_repo_name_clashes(cleaned_https_deps)
            
            just_cloned += clone_new_deps(list(all_deps), deps_folder)
            child_deps = set(find_child_dependencies(project_folder))
            new_all_deps = all_deps.union(child_deps)            
            
            if new_all_deps == all_deps:
                break;
            else:
                all_deps = new_all_deps

        pull_dep_changes(deps_folder, just_cloned)
        write_new_requirements_file(matlab_requirements_file, cleaned_https_deps)
        # write_addpath(deps_folder, new_deps_folder, project_src_folder, addpath_script)
        # if current project folder is not a git repo, initialize git repo
        write_gitignore(gitignore_file)
        if not os.path.isdir(os.path.join(project_folder,'.git')):
            top_repo = git.Repo.init(project_folder)
    else:
        print "Folder does not contain a matlab_requirements.txt! Are you sure this is a project folder?"
    
    
