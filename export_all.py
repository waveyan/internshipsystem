# because of the PWD environment variables, this script CAN NOT run on itself
import os, ast

with open('export_all.list', 'r') as f:
    file_list = f.readline().strip('\n')
    root_path = f.readline().strip('\n')
    root_path_2 = f.readline()
file_list = ast.literal_eval(file_list)

# 建立文件
for x in file_list:
    root_path_3 = os.path.join(root_path_2, x['grade'], x['major'], x['stuId']+'_'+x['stuName'], x['comName'])
    os.system('mkdir -p %s' % root_path_3)
    os.system('cp -r %s/* %s %s %s' % (x['storage_path'], x['intern_path'], x['journal_path'], root_path_3))
    # 更改中文名
    os.system('mv %s/summary_doc %s/总结文档' % (root_path_3, root_path_3))
    os.system('mv %s/attachment %s/附件' % (root_path_3, root_path_3))
    os.system('mv %s/agreement %s/实习协议书' % (root_path_3, root_path_3))
    os.system('mv %s/visit %s/探访记录' % (root_path_3, root_path_3))
    os.system('mv %s/score_img/comscore %s/score_img/企业评分' % (root_path_3, root_path_3))
    os.system('mv %s/score_img/schscore %s/score_img/校内评分' % (root_path_3, root_path_3))
    os.system('mv %s/score_img %s/评分' % (root_path_3, root_path_3))
    os.system('mv %s/internlist* %s/%s_实习信息.xls' % (root_path_3, root_path_3, x['comName']))
    os.system('mv %s/journalList* %s/%s_实习日志.xls' % (root_path_3, root_path_3, x['comName']))
# 打包zip文件
zip_folder = os.path.basename(root_path_2)
zip_file = '%s.zip' % zip_folder
zip_path = os.path.join(root_path, zip_file)
print ('zip_folder:', zip_folder, 'zip_file:', zip_file, 'zip_path:', zip_path)
os.system('cd %s; zip -0r %s %s' %(root_path, zip_file, zip_folder))
#os.system('zip -0r %s %s' %(zip_path, root_path_2))
