import copy

id = '5' 

orchestration_rule_rules = [
    {
        'id': '1', 
        'actions': ['a__b__c_d_e_rules[2,4]']
    },
    {
        'id': '2', 
        'actions': ['a__b__c_d_e']
    },
    {
        'id': '3', 
        'actions': ['a__b__c_d_e_f']
    },
    {
        'id': '4', 
        'actions': ['a__b']
    }
]

orchestration_rule_rules = [rule for rule in orchestration_rule_rules if str(rule['id']) != str(id)]
orchestration_rule_rules_new = []

for rule in orchestration_rule_rules[:]:
    new_rule = copy.deepcopy(rule)
    new_rule['actions'] = []
    if int(rule['id']) > int(id):
        new_rule['id'] = str(int(rule['id']) - 1)
    for action in rule['actions']:
        action_parts = action.split('__')  
        new_action = action_parts[0] + '__' +  action_parts[1]
        if len(action_parts) == 3:
            if 'rules[' in action_parts[2]:            
                action_params = str(action_parts[2]).split('_')
                new_action_params = ''
                for action_param in action_params:
                    if 'rules[' in action_param:
                        action_param_rules = action_param.replace('rules[', '').replace(']', '').split(',')
                        for action_param_rule in action_param_rules[:]:
                            if int(action_param_rule) == int(id):
                                action_param_rules.remove(str(action_param_rule))
                            elif int(action_param_rule) > int(id):
                                action_param_rules.remove(str(action_param_rule))
                                action_param_rules.append(str(int(action_param_rule) - 1))
                        new_action_params += 'rules['   
                        for action_param_rule in action_param_rules:
                            new_action_params += action_param_rule + ','
                        new_action_params = new_action_params[:-1]
                        new_action_params += ']_'
                    else:
                        new_action_params += action_param + '_'
                new_action += '__' +  new_action_params[:-1]
            else:    
                new_action += '__' +  action_parts[2]            
        new_rule['actions'].append(new_action)
    orchestration_rule_rules_new.append(new_rule)
    
print('orchestration_rule_rules_new', orchestration_rule_rules_new)
