import pandas as pd    
from bs4 import BeautifulSoup


def read_bpmn(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        bpmn_content = file.read()

    soup = BeautifulSoup(bpmn_content, 'xml')
    
    process_data = []

    processes = soup.find_all('bpmn:process')
    for process in processes:
            
        elements = process.find_all(['bpmn:parallelGateway', 'bpmn:startEvent', 'bpmn:endEvent', 'bpmn:task', 
                                      'bpmn:userTask', 'bpmn:serviceTask', 'bpmn:exclusiveGateway'])
        
        
        x_block_dict = {}
        x_blocks = process.find_all(['bpmn:parallelGateway'])
        for x_block in x_blocks:
            x_block_id = x_block.get('id', 'Неизвестная ссылка')
            x_block_outgoings = x_block.find_all(['bpmn:incoming'])
            for x_block_outgoing in x_block_outgoings:
                if x_block_dict.get(x_block_id):
                    x_block_dict[x_block_outgoing.string].append(x_block_id)
                else: 
                    x_block_dict[x_block_outgoing.string]= [x_block_id]

            
        
        arrows_flows = {}
        arrows = process.find_all(['bpmn:sequenceFlow'])
        for arrow in arrows:
            
            arrow_id = arrow.get('id', 'Неизвестная ссылка')
            target_to = arrow.get('targetRef', 'Неизвестная ссылка')
            if arrows_flows.get(arrow_id):
                arrows_flows[arrow_id].append(target_to)
            else: 
                arrows_flows[arrow_id] = [target_to]
                
        gr_dict = {}
        for arrow in arrows:
            
            arrow_in = arrow.get('sourceRef', 'Неизвестная ссылка')
            target_to = arrow.get('targetRef', 'Неизвестная ссылка')
            if gr_dict.get(arrow_in):
                gr_dict[arrow_in].append(target_to)
            else: 
                gr_dict[arrow_in] = [target_to]
        
        
        arrows_ins = {}
        for arrow in arrows:
            target_from = arrow.get('sourceRef', 'Неизвестная ссылка')
            arrow_id = arrow.get('id', 'Неизвестная ссылка')
            
            if arrows_ins.get(arrow_id):
                arrows_ins[arrow_id].append(target_from)
            else: 
                arrows_ins[arrow_id] = [target_from]
        
        
        associations_list = []
        associations = process.find_all(['bpmn:association'])
        for association in associations:
            association_to = association.get('sourceRef', 'Неизвестная ссылка')
            target_id = association.get('targetRef', 'Неизвестная ссылка')
            associations_list.append([association_to, target_id])
     
        
    
        annotations = process.find_all('bpmn:textAnnotation')
        if annotations: 
            for annotation in annotations:
                annotation_id = annotation.get('id', 'Неизвестный ID')
                annotation_text = annotation.find('bpmn:text').string if annotation.find('bpmn:text') else 'Нет текста'
                for i in associations_list:
                    if i[1] ==annotation_id: i.append(annotation_text)

        
        elements_dict = {}
        for element in elements:
            element_id = element['id']
            element_name = element.get('name', element_id)
            elements_dict.update({element_id:element_name})
            
            text = []            
            for i in associations_list:
                if i[0] == element_id:
                    text.append(i[2])


            incoming_flows = element.find_all('bpmn:incoming')
            incoming_ids = [flow.string for flow in incoming_flows]


            outgoing_flows = element.find_all('bpmn:outgoing')
            outgoing_ids = [flow.string for flow in outgoing_flows]

            
            start_events = process.find_all('bpmn:startEvent')
            user_tasks = process.find_all('bpmn:userTask')
            service_tasks = process.find_all('bpmn:serviceTask')
            exclusive_gateways = process.find_all('bpmn:exclusiveGateway')
            xs_blocks = process.find_all(['bpmn:parallelGateway'])
            
            end_events_dict = {}
            end_events = process.find_all('bpmn:endEvent')
            for end_event in end_events:
                end_event_id = end_event.get('id', 'Неизвестная ссылка')
                if end_events_dict.get(end_event_id):
                    end_events_dict[end_event_id].append([])
                else: 
                    end_events_dict[end_event_id] = [] 
            if element in start_events:
                element['operation_type'] = 'Начало'
            elif element in user_tasks:
                element['operation_type'] = 'Действие'
            elif element in service_tasks:
                element['operation_type'] = 'Условие'
            elif element in exclusive_gateways:
                element['operation_type'] = 'Слияние/разделение'
            elif element in end_events:
                element['operation_type'] = 'Конец'
            elif element in xs_blocks:
                element['operation_type'] = 'Слияние/разделение'
            else: element['operation_type'] = 'Неизвестный тип'
                                           
            
            element_data = [element_name, incoming_ids, outgoing_ids, element['operation_type'], text]
            process_data.append(element_data)
        
    return process_data, arrows_flows, arrows_ins, x_block_dict, gr_dict, end_events_dict, elements_dict


bpmn_file_path = './program.bpmn'

result, arrows_flows, arrows_ins, x_block_dict, gr_dict, end_events_dict, elements_dict = read_bpmn(bpmn_file_path)
    
operation_name, incomings, outgoings, operation_type, text_annotation = zip(*result)


operation_name = list(operation_name)
incomings = list(incomings)
outgoings = list(outgoings)
operation_type = list(operation_type)
text_annotation = list(text_annotation)

visited = []
node_dict = {}
def dfs(node, prefix, number):
    if node in visited:
        return
    visited.append(node)

    # Получаем соседей
    neighbors = gr_dict.get(node, [])
    number_of_neighbors = len(neighbors)
    
    node_dict[node] = f"{prefix}{number}"

    # Выводим узел с текущим номером
    print(f"{prefix}{number} - {node}")

    if number_of_neighbors > 1:
        # Если у узла есть соседи, добавляем префикс для вложенных узлов
        for i, neighbor in enumerate(neighbors):
            dfs(neighbor, f"{prefix}{number}.{i + 1}.", 1) # Используем текущий номер
    elif number_of_neighbors == 1:
        dfs(neighbors[0], prefix, number + 1)


dfs('StartEvent_1', '', 1)


print('ffffffffffffffffffffffffffffffffffffff', node_dict)
print('fddddddddddddddddddddddddddddddddddddd', elements_dict)

numbers = {}
for x, naming in elements_dict.items():
    if x in node_dict:
        numbers[naming] = node_dict[x]
    else:
        numbers[naming] = ''
print('nnnnnnnnnnnnnnnnnnnnnnnnnnnn',numbers)



new_outgoings = []
for i in outgoings:
    current_outgoings = []
    for x in i:
        current_outgoings.append(arrows_flows[x])
    numb_list = []
    for y in current_outgoings:
        for name, numb in node_dict.items():
            if name in y:
                numb_list.append(numb)
    new_outgoings.append(numb_list)

new_incomings = []
for i in incomings:
    current_incomings = []
    for x in i:
        current_incomings.append(arrows_ins[x])
    numb_lis = []
    for y in current_incomings:
        for name, numb in node_dict.items():
            if name in y:
                numb_lis.append(numb)
    new_incomings.append(numb_lis)

graph = arrows_flows


numbering = []
    
  
# for i, y in node_dict.items():
#     if i in numbers.keys():
#         numbering.append(numbers[i])
#     else:
#         numbering.append(None) 

# operation_name_1 = [i for i in numbers.keys()]

    
# print(operation_name_1)
# print(numbering)

print('ooooooooooooooooooooooo', operation_name)

operation_name_for_excel = []
operation_s = [m for t,m in elements_dict.items()]
for i in operation_s:
    if 'Gateway' not in i:
        operation_name_for_excel.append(i)
    else: operation_name_for_excel.append('Блок слияния или разделения')

for i, y in elements_dict.items():
    for o, p in node_dict.items():
        if i == o:
            numbering.append(p)    





df = pd.DataFrame({
        '#': numbering, 
        'Тип': operation_type, 
        'Название этапа': operation_name_for_excel,
        'Свойство': [','.join(i) for i in text_annotation],
        '# Входы': ['   |   '.join(i) for i in new_incomings], 
        '# Выходы': ['   |   '.join(i) for i in new_outgoings],
        'Ожидание': [" " if i == "Условие" or i == "Действие" else '-' for i in operation_type], 
        'Факт': [" " if i == "Условие" or i == "Действие" else '-' for i in operation_type], 
        'Соответствует?': ['Да    / Нет     '] * len(operation_name)
    })
df.sort_values(by='#', ascending=True, inplace=True)
df.to_excel('output.xlsx', index=False)