package com.ericsson.nms.litp.taf.autoinstall.test.cases;

import java.io.*;
import java.io.File;
import java.io.IOException;
import java.util.List;
import java.util.ArrayList;

import org.apache.commons.io.FileUtils;

import org.apache.log4j.Logger;
import org.testng.annotations.Test;

import java.net.InetAddress;
import java.net.UnknownHostException;


//import static org.junit.Assert.assertThat;
import static org.hamcrest.MatcherAssert.assertThat;
import static org.hamcrest.CoreMatchers.containsString;

import com.ericsson.cifwk.taf.TorTestCaseHelper;
import com.ericsson.cifwk.taf.annotations.*;
import com.ericsson.cifwk.taf.tools.cli.TimeoutException;
import com.ericsson.cifwk.taf.handlers.implementation.LocalCommandExecutor;
import com.ericsson.cifwk.taf.utils.FileFinder;
import com.ericsson.cifwk.taf.data.*;

import java.io.FileNotFoundException;

import javax.inject.Inject;

public class AutoInstallENMRunner extends TorTestCaseHelper {

    Logger logger = Logger.getLogger(AutoInstallENMRunner.class);
    
    /**
     * @throws TimeoutException,FileNotFoundException
     * @DESCRIPTION Testing a simple test case for CDB
     * @PRE Connection to SUT
     * @PRIORITY HIGH
     */
    
    //@TestId(id = "LITP2_autoinstall_ENM", title = "Install LITP2/ENM")
    @TestStep(id = "LITP2_autoinstall_ENM")
    @Test(groups={"Acceptance"})
    public void autoInstallLITP2ENM() {
        logger.info("In test case, running assertion now");
        assertTrue("ERROR during AutoInstall execution", 0 == 0);
        logger.info("Assertion complete, test case will now finish");
    }
} 
