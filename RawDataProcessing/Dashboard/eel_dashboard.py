#%%
import eel
import ast
eel.init('web')

@eel.expose
def create_incfiles(output: dict):
    to_dict = ast.literal_eval(output)
    with open('output.txt', 'w') as f:
        f.write('Type of output: ')
        f.write(str(type(output))+'\n')
        f.write('Type of conversion: ')
        f.write(str(type(to_dict))+'\n')
        f.write('Output:\n')
        f.write(str(to_dict))

eel.start('index.html', size=(900,620), position=(500,200))