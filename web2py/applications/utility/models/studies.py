options.update({
    'fitts' : {
        'price' : [.01, .00, .03],
        'style' : ['classic fitts'],
        'width' : [300,  30, 3],
        'num_tasks' : 10
        },

#     'my_crazy_hit' : {
#         'price' : [.01, .03],
#         'style' : ['amazing', 'retarded', 'aphrodesiac']
#         }
    })


########### Example study launch (put yours in a <task>.py file, not here)
def launch_fitts(num_hits, name, description):
    task = 'fitts'
    conditions = {
        'price' : [.00, .06, .01],
        'style' : ['classic fitts'], #'scattered'],
        'width' : [300],
        'num_tasks' : [40]
        }
    launch_study(num_hits, task, conditions, name, description)
