import os
import argparse

ADD = 0b0010
SUB = 0b0110
AND = 0b0000
OR = 0b0001
MemSize = 1000 

class InsMem(object):
    def __init__(self, name, ioDir):
        self.id = name
        with open(ioDir + "/imem.txt") as im:
            self.IMem = [data.replace("\n", "") for data in im.readlines()]
        while len(self.IMem) < MemSize: 
            self.IMem.append('00000000')

    def readInstr(self, ReadAddress):
        instr = ''
        for i in range(4): 
            instr += self.IMem[ReadAddress + i]
        return instr
          
class DataMem(object):
    def __init__(self, name, ioDir):
        self.id = name
        self.ioDir = ioDir
        with open(ioDir + "/dmem.txt") as dm:
            self.DMem = [data.replace("\n", "") for data in dm.readlines()]
        while len(self.DMem) < MemSize: 
            self.DMem.append('00000000')

    def readDataMem(self, ReadAddress):
        if isinstance(ReadAddress, str): 
            ReadAddress = bitstr_to_int(ReadAddress)

        data = ''
        for i in range(4): 
            data += self.DMem[ReadAddress + i]
        return data
        
    def writeDataMem(self, Address, WriteData):
        if isinstance(WriteData, int): 
            WriteData = int_to_bitstr(WriteData)
        if isinstance(Address, str): 
            Address = bitstr_to_int(Address)

        parsedData = [WriteData[:8], WriteData[8:16], WriteData[16:24], WriteData[24:]]
        for i in range(4): 
            self.DMem[Address + i] = parsedData[i]
                     
    def outputDataMem(self):
        resPath = self.ioDir + "/" + self.id + "_DMEMResult.txt"
        with open(resPath, "w") as rp:
            rp.writelines([str(data) + "\n" for data in self.DMem])

class RegisterFile(object):
    def __init__(self, ioDir):
        self.outputFile = ioDir + "RFResult.txt"
        self.Registers = ['0'*32 for i in range(32)]
    
    def readRF(self, Reg_addr):
        if isinstance(Reg_addr, str): 
            Reg_addr = bitstr_to_int(Reg_addr)

        return self.Registers[Reg_addr]
    
    def writeRF(self, Reg_addr, Wrt_reg_data):
        if isinstance(Wrt_reg_data, int): 
            Wrt_reg_data = int_to_bitstr(Wrt_reg_data)
        self.Registers[Reg_addr] = Wrt_reg_data
         
    def outputRF(self, cycle):
        op = ["State of RF after executing cycle:" + str(cycle) + "\n"]
        op.extend([val+"\n" for val in self.Registers])
        if(cycle == 0): perm = "w"
        else: perm = "a"
        with open(self.outputFile, perm) as file:
            file.writelines(op)

class State(object):
    def __init__(self):
        self.IF = {"nop": False, "PC": 0, 'PCSrc': 0, 'PCWrite': 1, 'Flush': 0}
        self.ID = {"nop": False, 'PC': 0, "Instr": '0', "Rs1": 0, "Rs2": 0, "Rd": 0,}
        self.EX = {"nop": False, 'Ins': '', "Read_data1": 0, "Read_data2": 0, "Imm": 0, "Rs1": 0, "Rs2": 0, "Rd": 0, 'funct7': '', 'funct3': '', 'opcode': '', 'ALUoutput': '0', "Branch": 0, "MemRead": 0, "MemtoReg": 0, "ALUOp": 0, 'MemWrite': 0, 'ALUSrc': 0, 'RegWrite': 0}
        self.MEM = {"nop": False, "ALUoutput": 0, 'Read_data2': 0, 'Load_data': 0, "Rs1": 0, "Rs2": 0, 'Rd': 0, "MemtoReg": 0, "MemRead": 0, "MemWrite": 0, "RegWrite": 0}
        self.WB = {"nop": False, "ALUoutput": 0, 'Write_data': 0, "Rs1": 0, "Rs2": 0, "Rd": 0, "RegWrite": 0, 'MemtoReg': 0}

class Core(object):
    def __init__(self, ioDir, imem, dmem):
        self.myRF = RegisterFile(ioDir)
        self.cycle = 0
        self.halted = False
        self.ioDir = ioDir
        self.state = State()
        self.nextState = State()
        self.ext_imem = imem
        self.ext_dmem = dmem

    def assign_value(self, ioDir, imem, dmem):
        self.ioDir = ioDir
        self.ext_imem = imem
        self.ext_dmem = dmem


class SingleStageCore(Core):
    def __init__(self, ioDir, imem, dmem):
        super(SingleStageCore, self).__init__(ioDir + "\\SS_", imem, dmem)
        self.opFilePath = ioDir + "\\StateResult_SS1.txt"

    def step(self):
        if self.state.IF["nop"]:
            self.halted = True
        PC = self.state.IF['PC']
        instr = self.ext_imem.readInstr(PC)

        func7 = instr[:7]
        func3 = instr[17:20]
        opcode = instr[25:]
        rs1 = instr[12:17]
        rs2 = instr[7:12]
        rd = instr[20:25]

        ins = ''
        type = ''
        if opcode == '0110011':
            if func3 == '000':
                if func7 == '0000000':
                    ins = 'ADD'
                elif func7 == '0100000':
                    ins = 'SUB'
            elif func3 == '100':
                ins = 'XOR'
            elif func3 == '110':
                ins = 'OR'
            elif func3 == '111':
                ins = 'AND'
            type = 'R'
        elif opcode == '0010011' or opcode == '0000011':
            if func3 == '000': 
                if opcode == '0010011': 
                    ins = 'ADDI'
                elif opcode == '0000011': 
                    ins = 'LW'
            elif func3 == '100': 
                ins =  'XORI'
            elif func3 == '110': 
                ins =  'ORI'
            elif func3 == '111': 
                ins = 'ANDI'
            type = 'I'
        elif opcode == '1101111':
            ins = 'JAL'
            type = 'J'
        elif opcode == '1100011':
            if func3 == '000': 
                ins = 'BEQ'
            elif func3 == '001': 
                ins = 'BNE'
            type = 'B'
        elif opcode == '0100011':
            ins = 'SW'
            type = 'S'
        elif opcode == '1111111':
            ins = 'HALT'
            type = 'H'
        imm_raw = getImm(instr, type)
        rs2 = int(rs2, 2)
        rs1 = int(rs1, 2)

        rd = int(rd, 2)
        imm = bitstr_to_int(imm_raw)
        if type == 'H':
            self.state.IF['nop'] = True
            self.state.ID['nop'] = True
            self.state.EX['nop'] = True
            self.state.MEM['nop'] = True
            self.state.WB['nop'] = True
        self.state.ID['Instr'] = instr

        rs1_data = self.myRF.readRF(rs1)
        rs2_data = self.myRF.readRF(rs2)
        if type == 'J':
            rs1_data = int_to_bitstr(PC)
            rs2_data = int_to_bitstr(4)
        
        main = {
            'branch': 0,
            'MemRead': 0,
            'MemtoReg': 0,
            'ALUOp': 0,
            'MemWrite': 0,
            'ALUSrc': 0,
            'RegWrite': 0
        }

        if type == 'R':
            main["RegWrite"] = 1
            main["ALUOp"] = 0b10
        elif type == 'I':
            main["ALUSrc"] = 1
            main["RegWrite"] = 1
            main["ALUOp"] = 0b10
            if ins == 'LW':
                main["MemRead"] = 1
                main["MemtoReg"] = 1
        elif type == 'S':
            main["ALUSrc"] = 1
            main["MemWrite"] = 1
            main["ALUOp"] = 0b00
        elif type == 'B':
            main["branch"] = 1
            main["ALUOp"] = 0b01
        elif type == 'J':
            main["RegWrite"] = 1
            main["branch"] = 1
            main["ALUOp"] = 0b10

        ALU_con = 0b0010
        if main["ALUOp"] == 0b00:
            ALU_con = 0b0010
        elif main["ALUOp"] == 0b01:
            ALU_con = 0b0110
        elif main["ALUOp"] == 0b10: 
            if opcode == '1101111':
                ALU_con = 0b0010
            elif func7 == '0100000': 
                ALU_con = 0b0110
            elif func3 == '000': 
                ALU_con = 0b0010
            elif func3 == '111': 
                ALU_con = 0b0000
            elif func3 == '110' or func3 == '100': 
                ALU_con = 0b0001
            else: 
                ALU_con = 0b0010
        else: 
            ALU_con = 0b0010
        input2 = imm_raw if main["ALUSrc"] else rs2_data
        alu_output = ALU(ALU_con, ins, rs1_data, input2)

        if type != 'H':
            if ins == 'BEQ':
                alu_output = alu_output == 0
            elif ins == 'BNE':
                alu_output = alu_output != 0
            branch_logic_date = main["branch"] and alu_output
            self.nextState.IF['PC'] = PC + imm if branch_logic_date else PC + 4
            self.state.IF['PC'] = self.nextState.IF['PC']

        self.state.EX = {
            "nop": False, 
            "Read_data1": rs1_data, 
            "Read_data2": rs2_data, 
            "Imm": imm, 
            "Rs": rs1, 
            "Rt": rs2, 
            "Wrt_reg_addr": main["MemtoReg"], 
            "rd_mem": main["MemRead"],
            "wrt_mem": main["MemWrite"], 
            "alu_op": main["ALUOp"], 
            "wrt_enable": main["RegWrite"], 
            }   

        lw_value = 0
        alu_output_raw = int_to_bitstr(alu_output)

        if main["MemWrite"]:
            self.ext_dmem.writeDataMem(alu_output_raw, rs2_data)
        elif main["MemRead"]:
            lw_value = self.ext_dmem.readDataMem(alu_output_raw)
        
        wb_value = lw_value if main["MemtoReg"] else alu_output_raw
        self.state.MEM['ALUresult'] = alu_output_raw
        self.state.MEM['Store_data'] = rs2
        self.state.MEM['Rs'] = rs1
        self.state.MEM['Rt'] = rs2
        self.state.MEM['Wrt_reg_addr'] = main["MemtoReg"]
        self.state.MEM['rd_mem'] = main["MemRead"]

        if main["RegWrite"]:
            self.myRF.writeRF(rd, wb_value)
        
        self.state.WB['wrt_data'] = wb_value
        self.state.WB['Rs'] = rs1
        self.state.WB['Rt'] = rs2
        self.state.WB['Wrt_reg_addr'] = main["MemtoReg"]
        self.state.WB['wrt_enable'] = main["RegWrite"]
            
        self.myRF.outputRF(self.cycle) # dump RF
        self.printState(self.nextState, self.cycle) # print states after executing cycle 0, cycle 1, cycle 2 ... 
            
        self.state = self.nextState #The end of the cycle and updates the current state with the values calculated in this cycle
        self.cycle += 1

    def printState(self, state, cycle):
        printstate = ["-"*50+"\n", "State after executing cycle: " + str(cycle) + "\n"]
        for key in self.state.IF.keys(): 
            printstate.append("IF.{}: {}\n".format(key, state.IF[key]))
        printstate.append('\n')
        for key in state.ID.keys(): 
            printstate.append("ID.{}: {}\n".format(key, state.ID[key]))
        printstate.append('\n')
        for key in state.EX.keys(): 
            printstate.append("EX.{}: {}\n".format(key, state.EX[key]))
        printstate.append('\n')
        for key in state.MEM.keys(): 
            printstate.append("MEM.{}: {}\n".format(key, state.MEM[key]))
        printstate.append('\n')
        for key in state.WB.keys(): 
            printstate.append("WB.{}: {}\n".format(key, state.WB[key]))
        
        if(cycle == 0): perm = "w"
        else: perm = "a"
        with open(self.opFilePath, perm) as wf:
            wf.writelines(printstate)

class FiveStageCore(Core):
    def __init__(self, ioDir, imem, dmem):
        super(FiveStageCore, self).__init__(ioDir + "\\FS_", imem, dmem)
        self.opFilePath = ioDir + "\\StateResult_FS.txt"
        self.state.ID['nop'] = True
        self.state.EX['nop'] = True
        self.state.MEM['nop'] = True
        self.state.WB['nop'] = True

    def step(self):
    
        if self.state.IF["nop"] and self.state.ID["nop"] and self.state.EX["nop"] and self.state.MEM["nop"] and self.state.WB["nop"]:
            self.halted = True

        # --------------------- ID stage ---------------------
        if not self.state.WB['nop']: 
            wb_value = self.state.WB['Write_data'] if self.state.WB['MemtoReg'] else self.state.WB['ALUoutput']
            if self.state.WB['RegWrite'] and self.state.WB['Rd'] != 0: 
                self.myRF.writeRF(self.state.WB['Rd'], wb_value)

        if not self.state.MEM['nop']: 
            rs2_data_raw = self.state.MEM['Read_data2']
            MemWrite = self.state.MEM['MemWrite']
            MemRead = self.state.MEM['MemRead']
            ALU_output_raw = self.state.MEM['ALUoutput']
            lw_value = 0

            if MemWrite: 
                self.ext_dmem.writeDataMem(ALU_output_raw, rs2_data_raw)
            elif MemRead: 
                lw_value = self.ext_dmem.readDataMem(ALU_output_raw)

            self.nextState.WB['nop'] = False
            self.nextState.WB['Rs1'] = self.state.MEM['Rs1']
            self.nextState.WB['Rs2'] = self.state.MEM['Rs2']
            self.nextState.WB['Rd'] = self.state.MEM['Rd']
            self.nextState.WB['RegWrite'] = self.state.MEM['RegWrite']
            self.nextState.WB['MemtoReg'] = self.state.MEM['MemtoReg']
            self.nextState.WB['ALUoutput'] = self.state.MEM['ALUoutput']
            self.state.MEM['Load_data'] = lw_value
            self.nextState.WB['Write_data'] = lw_value
            self.nextState.WB['nop'] = False
            self.nextState.MEM['nop'] = True
        else:
            self.nextState.WB['nop'] = True
        
        if not self.state.EX['nop']: 
            forwarding = self.forward_units()
            forwardA, forwardB = forwarding

            ins = self.state.EX['Ins']
            ALUOp = self.state.EX['ALUOp']
            rs1_data_raw = self.state.EX['Read_data1']
            rs2_data_raw = self.state.EX['Read_data2']
            imm_raw = self.state.EX['Imm']
            func7 = self.state.EX['funct7']
            func3 = self.state.EX['funct3']
            opcode = self.state.EX['opcode']

            ALU_con = self.ALU_control(opcode, func7, func3, ALUOp)
          
            input1_raw = self.EX_MUX_A(rs1_data_raw, forwardA)
            inputB_raw = self.EX_MUX_B(rs2_data_raw, forwardB)
            input2_raw = self.EX_MUX_2(inputB_raw, imm_raw)

            ALU_output_raw = ALU(ALU_con, ins, input1_raw, input2_raw)

            self.state.EX['ALUoutput'] = ALU_output_raw
            self.nextState.MEM['nop'] = False
            self.nextState.MEM['ALUoutput'] = ALU_output_raw
            self.nextState.MEM['Read_data2'] = inputB_raw
            self.nextState.MEM['Rs1'] = self.state.EX['Rs1']
            self.nextState.MEM['Rs2'] = self.state.EX['Rs2']
            self.nextState.MEM['Rd'] = self.state.EX['Rd']
            self.nextState.MEM['MemRead'] = self.state.EX['MemRead']
            self.nextState.MEM['MemWrite'] = self.state.EX['MemWrite']
            self.nextState.MEM['RegWrite'] = self.state.EX['RegWrite']
            self.nextState.MEM['MemtoReg'] = self.state.EX['MemtoReg']
            self.nextState.MEM['nop'] = False
            self.nextState.EX['nop'] = True
        else: 
            self.nextState.MEM['nop'] = True

        if not self.state.ID['nop']:
            if not self.state.IF['Flush']: 
                instr = self.state.ID['Instr']
                PC = self.state.ID['PC']
                instr = self.ext_imem.readInstr(PC)
                func7 = instr[:7]
                func3 = instr[17:20]
                opcode = instr[25:]
                rs1_raw = instr[12:17]
                rs2_raw = instr[7:12]
                rd_raw = instr[20:25]
                ins = ''
                type = ''
                if opcode == '0110011':
                    if func3 == '000':
                        if func7 == '0000000':
                            ins = 'ADD'
                        elif func7 == '0100000':
                            ins = 'SUB'
                    elif func3 == '100':
                        ins = 'XOR'
                    elif func3 == '110':
                        ins = 'OR'
                    elif func3 == '111':
                        ins = 'AND'
                    type = 'R'
                elif opcode == '0010011' or opcode == '0000011':
                    if func3 == '000': 
                        if opcode == '0010011': 
                            ins = 'ADDI'
                        elif opcode == '0000011': 
                            ins = 'LW'
                    elif func3 == '100': 
                        ins =  'XORI'
                    elif func3 == '110': 
                        ins =  'ORI'
                    elif func3 == '111': 
                        ins = 'ANDI'
                    type = 'I'
                elif opcode == '1101111':
                    ins = 'JAL'
                    type = 'J'
                elif opcode == '1100011':
                    if func3 == '000': 
                        ins = 'BEQ'
                    elif func3 == '001': 
                        ins = 'BNE'
                    type = 'B'
                elif opcode == '0100011':
                    ins = 'SW'
                    type = 'S'
                elif opcode == '1111111':
                    ins = 'HALT'
                    type = 'H'
                imm_raw = getImm(instr, type)
                rs2 = int(rs2_raw, 2)
                rs1 = int(rs1_raw, 2)
                rd = int(rd_raw, 2)
                rs1_data_raw = self.myRF.readRF(rs1)
                rs2_data_raw = self.myRF.readRF(rs2)
                if type == 'J': 
                    rs1_data_raw = int_to_bitstr(PC)
                    rs2_data_raw = int_to_bitstr(4)

                self.state.ID['Rs1'] = rs1
                self.state.ID['Rs2'] = rs2
                self.state.ID['Rd'] = rd

                main = {
                    'branch': 0,
                    'MemRead': 0,
                    'MemtoReg': 0,
                    'ALUOp': 0,
                    'MemWrite': 0,
                    'ALUSrc': 0,
                    'RegWrite': 0
                }
                if type == 'R':
                    main["RegWrite"] = 1
                    main["ALUOp"] = 0b10
                elif type == 'I':
                    main["ALUSrc"] = 1
                    main["RegWrite"] = 1
                    main["ALUOp"] = 0b10
                    if ins == 'LW':
                        main["MemRead"] = 1
                        main["MemtoReg"] = 1
                elif type == 'S':
                    main["ALUSrc"] = 1
                    main["MemWrite"] = 1
                    main["ALUOp"] = 0b00
                elif type == 'B':
                    main["branch"] = 1
                    main["ALUOp"] = 0b01
                elif type == 'J':
                    main["RegWrite"] = 1
                    main["branch"] = 1
                    main["ALUOp"] = 0b10
                PCWrite, IF_IDWrite = self.hdu()
                self.state.IF['PCWrite'] = PCWrite
                if not PCWrite: 
                    main["branch"] = 0
                    main["MemRead"] = 0
                    main["MemtoReg"] = 0
                    main["ALUOp"] = 0
                    main["MemWrite"] = 0
                    main["ALUSrc"] = 0
                    main["RegWrite"] = 0

                jump = 1
                forwardA, forwardB = self.forward_branches()
                compare1_raw = self.id_mux1(rs1_data_raw, forwardA)
                compare2_raw = self.id_mux2(rs2_data_raw, forwardB)
                if ins == 'BEQ': 
                    jump = compare1_raw == compare2_raw
                elif ins == 'BNE': 
                    jump = compare1_raw != compare2_raw
                self.state.IF['PCSrc'] = main["branch"] and jump
                self.nextState.IF['PC'] = self.b_MUX(imm_raw, PCWrite)
                
                if type != 'H': 
                    if type != 'B':
                        self.nextState.EX['nop'] = False
                        self.nextState.EX['Ins'] = ins
                        self.nextState.EX['Read_data1'] = rs1_data_raw
                        self.nextState.EX['Read_data2'] = rs2_data_raw
                        self.nextState.EX['Imm'] = imm_raw
                        self.nextState.EX['Rs1'] = rs1
                        self.nextState.EX['Rs2'] = rs2
                        self.nextState.EX['Rd'] = rd
                        self.nextState.EX['funct3'] = func3
                        self.nextState.EX['funct7'] = func7
                        self.nextState.EX['opcode'] = opcode
                        self.nextState.EX['Branch'] = main["branch"]
                        self.nextState.EX['MemRead'] = main['MemRead']
                        self.nextState.EX['MemtoReg'] = main["MemtoReg"]
                        self.nextState.EX['ALUOp'] = main["ALUOp"]
                        self.nextState.EX['MemWrite'] = main["MemWrite"]
                        self.nextState.EX['ALUSrc'] = main["ALUSrc"]
                        self.nextState.EX['RegWrite'] = main["RegWrite"]
                    else: 
                        self.nextState.EX['nop'] = True

                    if IF_IDWrite: 
                        print('{}\t{}\tx{}\tx{}\tx{}\t{}'.format(self.cycle, ins, rd, rs1, rs2, bitstr_to_int(imm_raw)))
                    else: 
                        print('{}\tNOP'.format(self.cycle))
                        self.nextState.IF['PC'] = self.state.IF['PC']
                        self.nextState.ID = self.state.ID

                else: 
                    self.nextState.EX['nop'] = True
                    self.nextState.ID['nop'] = True
                    self.nextState.IF['nop'] = True
                    print('{}\tHALT'.format(self.cycle))
            else: 
                # NOP for branch taken
                self.nextState.IF['PC'] = self.state.IF['PC'] + 4
                self.nextState.ID = self.state.ID
                self.nextState.EX['nop'] = True
                print('{}\tNOP'.format(self.cycle))
        else: 
            self.nextState.EX['nop'] = True
        
        if not self.state.IF['nop']: 
            PC = self.state.IF['PC']
            instr = self.ext_imem.readInstr(PC)

            if self.state.IF['PCWrite']:
                self.nextState.ID['PC'] = PC

            if self.state.ID['nop'] == True: 
                self.nextState.IF['PC'] = PC + 4
            
            if self.state.IF['PCWrite']: 
                self.nextState.ID['Instr'] = instr
        else: 
            self.nextState.IF['nop'] = True
            self.nextState.ID['nop'] = True
        
        self.myRF.outputRF(self.cycle) # dump RF
        self.printState(self.nextState, self.cycle) # print states after executing cycle 0, cycle 1, cycle 2 ... 
        
        self.state = self.nextState
        self.nextState = State() #The end of the cycle and updates the current state with the values calculated in this cycle
        self.cycle += 1

    def printState(self, state, cycle):
        if not self.halted:
            printstate = ["-"*60+"\n", "State after executing cycle: " + str(cycle) + "\n"]
            printstate.extend(["IF." + key + ": " + str(val) + "\n" for key, val in state.IF.items()])
            printstate.extend(["ID." + key + ": " + str(val) + "\n" for key, val in state.ID.items()])
            printstate.extend(["EX." + key + ": " + str(val) + "\n" for key, val in state.EX.items()])
            printstate.extend(["MEM." + key + ": " + str(val) + "\n" for key, val in state.MEM.items()])
            printstate.extend(["WB." + key + ": " + str(val) + "\n" for key, val in state.WB.items()])

            if(cycle == 0): perm = "w"
            else: perm = "a"
            with open(self.opFilePath, perm) as wf:
                wf.writelines(printstate)

    def get_alu_con(self, ALUOp, opcode, func7, func3):
        if ALUOp == 0b00:
            ALU_con = 0b0010
        elif ALUOp == 0b01:
            ALU_con = 0b0110
        elif ALUOp == 0b10: 
            if opcode == '1101111':
                ALU_con = 0b0010
            elif func7 == '0100000': 
                ALU_con = 0b0110
            elif func3 == '000': 
                ALU_con = 0b0010
            elif func3 == '111': 
                ALU_con = 0b0000
            elif func3 == '110' or func3 == '100': 
                ALU_con = 0b0001
            else: 
                ALU_con = 0b0010
        else: 
            ALU_con = 0b0010
        return ALU_con

    def WB_MUX(self, ALU_output_raw, lw_value, MemtoReg): 
        if MemtoReg: 
            return lw_value
        return ALU_output_raw

    def WB_MUX(self, ALU_output_raw, lw_value, MemtoReg): 
        if MemtoReg: 
            return lw_value
        return ALU_output_raw

    def EX_MUX_A(self, rs1, forwardA):
        if forwardA == 0b00: 
            return rs1
        elif forwardA == 0b10: 
            return self.state.MEM['ALUoutput']
        elif forwardA == 0b01: 
            return self.state.WB['Write_data']

    def EX_MUX_B(self, rs2, forwardB): 
        if forwardB == 0b00: 
            return rs2
        elif forwardB == 0b10: 
            return self.state.MEM['ALUoutput']
        elif forwardB == 0b01: 
            return self.state.WB['Write_data']
    
    def EX_MUX_2(self, inputB, imm_raw):
        if self.state.EX['ALUSrc']:
            return imm_raw
        return inputB

    def c_MUX(self, main_con, PCWrite): 
        if not PCWrite: 
            main_con.stall()
        
    def b_MUX(self, imm_raw, PCWrite): 
        if PCWrite: 
            imm = bitstr_to_int(imm_raw)
            if self.state.IF['PCSrc']: 
                self.nextState.IF['Flush'] = 1
                return self.state.ID['PC'] + imm
            else: 
                return self.state.IF['PC'] + 4
        return self.state.ID['PC']
    
    def id_mux1(self, rs1, forwardA):
        if forwardA == 0b00: 
            return rs1
        elif forwardA == 0b10: 
            return self.state.EX['ALUoutput']
        elif forwardA == 0b01: 
            return self.state.MEM['Load_data']

    def id_mux2(self, rs2, forwardB): 
        if forwardB == 0b00: 
            return rs2
        elif forwardB == 0b10: 
            return self.state.EX['ALUoutput']
        elif forwardB == 0b01: 
            return self.state.MEM['Load_data']
    
    def forward_branches(self): 
        forwardA = 0
        forwardB = 0
        EX_MEM = self.state.MEM
        ID_EX = self.state.EX
        IF_ID = self.state.ID

        if (ID_EX['RegWrite'] and (ID_EX['Rd'] != 0) and (ID_EX['Rd'] == IF_ID['Rs1'])): 
            forwardA = 0b10

        if (ID_EX['RegWrite'] and (ID_EX['Rd'] != 0) and (ID_EX['Rd'] == IF_ID['Rs2'])):
            forwardB = 0b10

        if EX_MEM['RegWrite'] and (EX_MEM['Rd'] != 0) and not(ID_EX['RegWrite'] and (ID_EX['Rd'] != 0) and (ID_EX['Rd'] == IF_ID['Rs1'])) and (EX_MEM['Rd'] == IF_ID['Rs1']):
            forwardA = 0b01

        if (EX_MEM['RegWrite'] and (EX_MEM['Rd'] != 0) and not(ID_EX['RegWrite'] and (ID_EX['Rd'] != 0) and (ID_EX['Rd'] == IF_ID['Rs2'])) and (EX_MEM['Rd'] == EX_MEM['Rs2'])): 
            forwardB = 0b01
        
        return (forwardA, forwardB)

    def hdu(self): 
        ID_EX = self.state.EX
        IF_ID = self.state.ID
        PCWrite = True
        IF_IDWrite = True
        if ID_EX['MemRead'] and ((ID_EX['Rd'] == IF_ID['Rs1']) or (ID_EX['Rd'] == IF_ID['Rs2'])): 
            PCWrite = False
            IF_IDWrite = False
        return (PCWrite, IF_IDWrite)
    
    def forward_units(self): 
        forwardA = 0
        forwardB = 0
        EX_MEM = self.state.MEM
        MEM_WB = self.state.WB
        ID_EX = self.state.EX

        if (EX_MEM['RegWrite'] and (EX_MEM['Rd'] != 0) and (EX_MEM['Rd'] == ID_EX['Rs1'])): 
            forwardA = 0b10

        if (EX_MEM['RegWrite'] and (EX_MEM['Rd'] != 0) and (EX_MEM['Rd'] == ID_EX['Rs2'])):
            forwardB = 0b10

        if MEM_WB['RegWrite'] and (MEM_WB['Rd'] != 0) and not(EX_MEM['RegWrite'] and (EX_MEM['Rd'] != 0) and (EX_MEM['Rd'] == ID_EX['Rs1'])) and (MEM_WB['Rd'] == ID_EX['Rs1']):
            forwardA = 0b01

        if (MEM_WB['RegWrite'] and (MEM_WB['Rd'] != 0) and not(EX_MEM['RegWrite'] and (EX_MEM['Rd'] != 0) and (EX_MEM['Rd'] == ID_EX['Rs2'])) and (MEM_WB['Rd'] == ID_EX['Rs2'])): 
            forwardB = 0b01
        
        return (forwardA, forwardB)
    def ALU_control(self, opcode, funct7, funct3, ALUop):
        if ALUop == 0b00: 
            return ADD
        elif ALUop == 0b01: 
            return SUB
        elif ALUop == 0b10: 
            if opcode == '1101111':
                return ADD
            elif funct7 == '0100000': 
                return SUB
            elif funct3 == '000': 
                return ADD
            elif funct3 == '111': 
                return AND
            elif funct3 == '110' or funct3 == '100': 
                return OR
            else: 
                return ADD
        else: 
            return ADD

def int_to_bitstr(bit: int) ->str: 
    if type(bit) != int:
        if type(bit) ==  str: 
            while len(bit) < 32: 
                bit = '0' + bit 
            return bit
        else: 
            raise Exception('The input is neither a int nor a string')
    if bit < 0 : 
        reverse_bit = -bit - 1
        reverse_bitstr = bin(reverse_bit)[2:]
        bitstr = ''
        for bit in reverse_bitstr: 
            if bit == '1':
                bitstr += '0'
            else: 
                bitstr += '1'

        if len(bitstr) > 32:
            bitstr = bitstr[-32:]
        while len(bitstr) < 32: 
            bitstr = '1' + bitstr
    else: 
        bitstr = bin(bit)[2:]
        if len(bitstr) > 32:
            bitstr = bitstr[-32:]
        
        while len(bitstr) < 32: 
            bitstr = '0' + bitstr
    return bitstr

def bitstr_to_int(bitstr):
    if type(bitstr) ==  int: 
        return bitstr
    integer = int(bitstr, 2)
    bitlen = len(bitstr)
    if (integer & (1 << (bitlen - 1))) != 0:
        integer = integer - (1 << bitlen)
    return integer

def getImm(instr, type): 
    imm_raw = '0'
    if type == 'I': 
        imm_raw = instr[:12]
    
    elif type == 'S': 
        imm_raw = instr[:7] + instr[20:25]

    elif type == 'B': 
        imm_raw = instr[0] + instr[-8] + instr[1:7] + instr[20:24] + '0'

    elif type == 'J':
        imm_raw = instr[0] + instr[12:20] + instr[1:11] + '0'
    
    imm_raw = bitstr_to_int(imm_raw)
    imm_raw = int_to_bitstr(imm_raw)
    return imm_raw


def ALU(ALU_control, ins, input1_raw, input2_raw):
    input1 =  bitstr_to_int(input1_raw)
    input2 = bitstr_to_int(input2_raw)
    if ALU_control == 0b0010: 
        output = input1 + input2
    elif ALU_control == 0b0110: 
        output = input1 - input2
    elif ALU_control == 0b0000: 
        output = input1 & input2
    elif ALU_control == 0b0001: 
        if ins == 'OR' or ins == 'ORI': 
            output = input1 | input2
        else: 
            output = input1 ^ input2
    return int_to_bitstr(output)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='RV32I processor')
    parser.add_argument('--iodir', default="", type=str, help='Directory containing the input files.')
    args = parser.parse_args()

    ioDir = os.path.abspath(args.iodir)
    print("IO Directory:", ioDir)

    imem = InsMem("Imem", ioDir)
    dmem_ss = DataMem("SS", ioDir)
    dmem_fs = DataMem("FS", ioDir)
    
    ssCore = SingleStageCore(ioDir, imem, dmem_ss)
    fsCore = FiveStageCore(ioDir, imem, dmem_fs)

    while(True):
        # if not ssCore.halted:
            # ssCore.step()
        # if ssCore.halted:
        #     break
        if not fsCore.halted:
            fsCore.step()

        if fsCore.halted:
            break
    
    # dump SS and FS data mem.
    dmem_ss.outputDataMem()
    dmem_fs.outputDataMem()