"""
Convert the deprecated Caffe prototxt file to the current format
Author: Chi Chang - edingroot [at] gmail.com
"""
import sys
from prototxt_parser import PrototxtParser


def main():
    if len(sys.argv) == 3:
        srcpath = sys.argv[1]
        dstpath = sys.argv[2]
    else:
        srcpath = input("Source file: ")
        dstpath = input("Dest file: ")

    proto_parser = PrototxtParser()
    proto = proto_parser.parse(srcpath)

    # Process all 1st level scope and name is "layers"
    skip = False
    for attr in proto:
        if skip:
            skip = False
            continue

        if attr['type'] == 'scope' and attr['name'] == 'layers':
            attr['name'] = 'layer'

            blobs_lr_list = []
            weight_decay_list = []
            attrs = attr['attrs']
            i = 0
            while i < len(attrs):
                inner_attr = attrs[i]
                if inner_attr['type'] == 'attr' and inner_attr['name'] == 'blobs_lr':
                    blobs_lr_list.append(inner_attr['value'])
                    del attrs[i]
                elif inner_attr['type'] == 'attr' and inner_attr['name'] == 'weight_decay':
                    weight_decay_list.append(inner_attr['value'])
                    del attrs[i]
                else:
                    i += 1
            if len(blobs_lr_list) == len(weight_decay_list):
                for j in range(len(blobs_lr_list)):
                    param_scope = PrototxtParser.new_scope_object('param')
                    param_scope['attrs'].append(PrototxtParser.new_attr_object('lr_mult', blobs_lr_list[j]))
                    param_scope['attrs'].append(PrototxtParser.new_attr_object('decay_mult', weight_decay_list[j]))
                    attrs.append(param_scope)
            else:
                for j in range(len(blobs_lr_list)):
                    param_scope = PrototxtParser.new_scope_object('param')
                    param_scope['attrs'].append(PrototxtParser.new_attr_object('lr_mult', blobs_lr_list[j]))
                    attrs.append(param_scope)
                for j in range(len(weight_decay_list)):
                    param_scope = PrototxtParser.new_scope_object('param')
                    param_scope['attrs'].append(PrototxtParser.new_attr_object('decay_mult', weight_decay_list[j]))
                    attrs.append(param_scope)
    proto_parser.set_proto(proto)

    with open(dstpath, mode='w') as dstfile:
        dstfile.write(proto_parser.stringify())

    print('done')


if __name__ == '__main__':
    if sys.version_info[0] != 2:
        print('Please run with python2')
        exit(1)
    main()
